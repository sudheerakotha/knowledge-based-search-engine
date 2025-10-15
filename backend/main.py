from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import uvicorn

from document_processor import DocumentProcessor
from vector_store import VectorStore
from rag_engine import RAGEngine

# ==========================
# ENV + LOGGING SETUP
# ==========================
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("knowledge_base.log"), logging.StreamHandler()],
)
logger = logging.getLogger("main")

# ==========================
# FASTAPI APP CONFIG
# ==========================
app = FastAPI(
    title="Knowledge Base Search Engine",
    version="1.1.0",
    description="""
    ### 🧠 Retrieval-Augmented Generation (RAG) Search Engine

    This API combines semantic vector search and LLM reasoning to provide:
    - **Document Upload & Processing** (PDF, DOCX, TXT)
    - **Semantic Search** using Sentence Transformers
    - **LLM Synthesis** using OpenRouter (LLaMA 3) or OpenAI GPT models
    - **Automated Evaluation** of retrieval & synthesis quality
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ==========================
# CORS
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# COMPONENT INITIALIZATION
# ==========================
document_processor = DocumentProcessor()
vector_store = VectorStore()
rag_engine = RAGEngine()

# ==========================
# Pydantic Models
# ==========================
class QueryRequest(BaseModel):
    query: str
    max_results: Optional[int] = 2
    filters: Optional[Dict] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: float
    retrieval_score: Optional[float] = None
    synthesis_score: Optional[float] = None


class UploadResponse(BaseModel):
    message: str
    processed_files: List[str]
    total_chunks: int


# ==========================
# APP STARTUP
# ==========================
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("🚀 Starting Knowledge Base Search Engine...")
        await vector_store.initialize()
        logger.info("✅ Vector store initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {e}")
        raise


# ==========================
# ROUTES
# ==========================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Knowledge Base Search Engine API",
        "version": "1.1.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check for backend"""
    return {
        "status": "healthy",
        "vector_store_ready": vector_store.is_initialized,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process multiple documents into the knowledge base"""
    try:
        os.makedirs("uploads", exist_ok=True)
        processed_files, total_chunks = [], 0

        for file in files:
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".pdf", ".docx", ".txt"]:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

            file_path = f"uploads/{filename}"
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            chunks = await document_processor.process_document(file_path)
            await vector_store.add_documents(chunks, filename)
            processed_files.append(filename)
            total_chunks += len(chunks)
            os.remove(file_path)

        return UploadResponse(
            message=f"Processed {len(processed_files)} file(s) successfully.",
            processed_files=processed_files,
            total_chunks=total_chunks,
        )

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the knowledge base with RAG pipeline.
    Returns synthesized answer, retrieval accuracy, and synthesis quality.
    """
    try:
        if not vector_store.is_initialized:
            raise HTTPException(status_code=503, detail="Vector store not initialized")

        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # === 1️⃣ Retrieve relevant documents ===
        relevant_docs = await vector_store.search(
            request.query, request.max_results, request.filters
        )

        if not relevant_docs:
            return QueryResponse(
                answer="No relevant documents found.",
                sources=[],
                confidence=0.0,
                retrieval_score=0.0,
                synthesis_score=0.0,
            )

        # === 2️⃣ Generate synthesized answer ===
        answer, confidence = await rag_engine.generate_answer(request.query, relevant_docs)

        # === 3️⃣ Evaluate retrieval accuracy (average similarity) ===
        retrieval_score = (
            round(sum([doc["score"] for doc in relevant_docs]) / len(relevant_docs), 3)
            if relevant_docs
            else 0.0
        )

        # === 4️⃣ Evaluate synthesis quality using the RAG evaluator ===
        synthesis_score = await rag_engine.evaluate_synthesis_quality(request.query, answer)

        logger.info(
            f"Query processed: retrieval={retrieval_score}, synthesis={synthesis_score}, confidence={confidence}"
        )

        # === 5️⃣ Format response ===
        sources = [
            {
                "source": doc["metadata"].get("source", "Unknown"),
                "score": round(doc["score"], 3),
                "content": (
                    doc["content"][:250] + "..."
                    if len(doc["content"]) > 250
                    else doc["content"]
                ),
            }
            for doc in relevant_docs
        ]

        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            retrieval_score=retrieval_score,
            synthesis_score=synthesis_score,
        )

    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all documents"""
    try:
        return {"documents": await vector_store.list_documents()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/metadata")
async def get_documents_metadata():
    """Get metadata and stats"""
    try:
        return await vector_store.get_collection_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/advanced")
async def advanced_search(request: QueryRequest):
    """Perform advanced search with filters"""
    try:
        results = await vector_store.search(request.query, request.max_results, request.filters)
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_name}")
async def delete_document(document_name: str):
    """Delete a document from the vector database"""
    try:
        success = await vector_store.delete_document(document_name)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": f"Document '{document_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================
# RUN SERVER
# ==========================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
