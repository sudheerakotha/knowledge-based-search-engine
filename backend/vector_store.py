import os
import logging
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize the vector store"""
        try:
            logger.info("Initializing vector store...")

            os.makedirs(self.persist_directory, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )

            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

            self.is_initialized = True
            logger.info("✅ Vector store initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise

    async def add_documents(self, chunks: List[Dict], source_name: str):
        """Add document chunks to the vector store"""
        if not self.is_initialized:
            raise RuntimeError("Vector store not initialized")

        try:
            documents = []
            metadatas = []
            ids = []

            for i, chunk in enumerate(chunks):
                doc_id = f"{source_name}_{chunk['metadata']['chunk_index']}"

                documents.append(chunk["content"])
                metadatas.append({
                    **chunk["metadata"],
                    "source": source_name,
                    "chunk_id": doc_id
                })
                ids.append(doc_id)

            # ✅ Normalize metadata (ChromaDB disallows lists)
            for meta in metadatas:
                for key, value in list(meta.items()):
                    if isinstance(value, list):
                        meta[key] = ", ".join(map(str, value))

            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"✅ Added {len(chunks)} chunks from {source_name}")

        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    async def search(self, query: str, max_results: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for relevant documents with optional filters"""
        if not self.is_initialized:
            raise RuntimeError("Vector store not initialized")

        try:
            logger.info(f"🔍 Searching for: '{query[:60]}' ... with filters: {filters}")

            where_clause = self._build_where_clause(filters) if filters else None

            # ✅ Chroma expects None if no valid filters
            if not where_clause:
                where_clause = None

            results = self.collection.query(
                query_texts=[query],
                n_results=max_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )

            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "score": 1 - results["distances"][0][i]  # Convert distance → similarity
                    })

            logger.info(f"Found {len(formatted_results)} relevant results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise

    def _build_where_clause(self, filters: Dict) -> Dict:
        """Build ChromaDB where clause from filters"""
        where_clause = {}

        if "file_type" in filters:
            where_clause["file_type"] = filters["file_type"]

        if "date_from" in filters or "date_to" in filters:
            date_filter = {}
            if "date_from" in filters:
                date_filter["$gte"] = filters["date_from"]
            if "date_to" in filters:
                date_filter["$lte"] = filters["date_to"]
            where_clause["created_at"] = date_filter

        if "language" in filters:
            where_clause["language"] = filters["language"]

        if "topics" in filters:
            where_clause["topics"] = {"$in": filters["topics"]}

        if "source" in filters:
            where_clause["source"] = filters["source"]

        return where_clause

    async def list_documents(self) -> List[str]:
        """List all unique documents in the collection"""
        if not self.is_initialized:
            raise RuntimeError("Vector store not initialized")

        try:
            results = self.collection.get(include=["metadatas"])

            sources = set()
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "source" in metadata:
                        sources.add(metadata["source"])

            return list(sources)

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise

    async def delete_document(self, source_name: str) -> bool:
        """Delete all chunks of a specific document"""
        if not self.is_initialized:
            raise RuntimeError("Vector store not initialized")

        try:
            results = self.collection.get(
                where={"source": source_name},
                include=["metadatas"]
            )

            if not results["ids"]:
                return False

            self.collection.delete(ids=results["ids"])
            logger.info(f"🗑️ Deleted {len(results['ids'])} chunks from {source_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    async def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        if not self.is_initialized:
            raise RuntimeError("Vector store not initialized")

        try:
            count = self.collection.count()
            sources = await self.list_documents()

            return {
                "total_chunks": count,
                "total_documents": len(sources),
                "documents": sources
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise

    def reset_collection(self):
        """Reset the entire collection (use with caution)"""
        if not self.is_initialized:
            raise RuntimeError("Vector store not initialized")

        try:
            self.client.delete_collection("knowledge_base")
            self.collection = self.client.create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            logger.warning("⚠️ Collection reset successfully")

        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise

    # 🧪 NEW: Evaluation Metrics for Retrieval Accuracy
    def evaluate_retrieval(self, test_cases: List[Dict[str, Any]], k: int = 5) -> Dict[str, float]:
        """
        Evaluate retrieval accuracy on given test queries.
        test_cases = [
            {"query": "What is probability theory?", "relevant_docs": ["3 Probability theory.pdf"]},
            {"query": "Explain regression.", "relevant_docs": ["12 Principal Regression .pdf"]}
        ]
        Returns: {"precision_at_k": 0.8, "recall_at_k": 0.75, "mrr_at_k": 0.66}
        """
        import math

        total_prec, total_rec, total_rr = 0.0, 0.0, 0.0
        n = max(1, len(test_cases))

        for case in test_cases:
            q = case["query"]
            gold = set(case.get("relevant_docs", []))

            results = self.collection.query(
                query_texts=[q],
                n_results=k,
                include=["metadatas"]
            )

            metas = results.get("metadatas", [[]])[0]
            retrieved = [m.get("source", "Unknown") for m in metas]
            hit_set = gold.intersection(set(retrieved))

            prec = len(hit_set) / max(1, len(retrieved))
            rec = len(hit_set) / max(1, len(gold))

            rr = 0.0
            for idx, s in enumerate(retrieved, start=1):
                if s in gold:
                    rr = 1.0 / idx
                    break

            total_prec += prec
            total_rec += rec
            total_rr += rr

        return {
            "precision_at_k": round(total_prec / n, 4),
            "recall_at_k": round(total_rec / n, 4),
            "mrr_at_k": round(total_rr / n, 4)
        }
