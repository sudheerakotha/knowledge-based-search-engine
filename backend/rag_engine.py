import os
import logging
from openai import AsyncOpenAI
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
import re
import json
import numpy as np

load_dotenv()
logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self):
        """Initialize RAG engine with OpenRouter or OpenAI client"""
        use_openrouter = True  # switch easily if needed

        try:
            if use_openrouter:
                self.client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                )
                self.model = "meta-llama/llama-3-8b-instruct"
                logger.info("Using OpenRouter (LLaMA 3-8B Instruct)")
            
            self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))
            self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
            self.min_similarity_threshold = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.3"))

        except Exception as e:
            logger.error(f"Error initializing RAG Engine: {str(e)}")
            raise

    async def generate_answer(self, query: str, relevant_docs: List[Dict]) -> Tuple[str, float]:
        """Generate a context-grounded answer using RAG pipeline"""
        try:
            logger.info(f"🧠 Generating answer for query: {query[:60]}")

            # Step 1 — Filter documents by relevance threshold
            filtered_docs = self._filter_by_similarity(relevant_docs)
            if not filtered_docs:
                logger.warning("⚠️ No documents met similarity threshold")
                return (
                    "No relevant documents found. Please rephrase your question or upload more data.",
                    0.0,
                )

            # Step 2 — Prepare document context
            context = self._prepare_context(filtered_docs)

            # Step 3 — Expand query for retrieval improvement
            expanded_query = await self._expand_query(query)

            # Step 4 — Construct optimized prompt
            prompt = self._create_prompt(expanded_query, context)

            # Step 5 — Generate LLM response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an intelligent assistant specialized in answering based only on provided documents. "
                            "If the context is insufficient, clearly state that. Always stay factual and concise."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            answer = response.choices[0].message.content.strip()

            # Step 6 — Compute confidence from document relevance and answer quality
            confidence = self._calculate_confidence(filtered_docs, answer)

            logger.info(f"✅ Answer generated with confidence: {confidence}")
            return answer, confidence

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"Error generating answer: {str(e)}", 0.0

    # ============================================================
    # Supporting Methods
    # ============================================================

    def _prepare_context(self, relevant_docs: List[Dict]) -> str:
        """Prepare textual context from document chunks"""
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            source = doc["metadata"].get("source", "Unknown")
            score = doc["score"]
            content = re.sub(r"\s+", " ", doc["content"]).strip()
            context_parts.append(f"[Document {i} | Source: {source} | Relevance: {score:.2f}]\n{content}\n")
        return "\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Build LLM-ready prompt for retrieval-augmented answering"""
        return f"""
You are a document-based reasoning assistant.

Context:
{context}

User Question:
{query}

Instructions:
- Answer the question using ONLY the provided documents.
- Mention which document(s) support your response.
- If information is missing, clearly state that.
- Be concise yet coherent and logically structured.

Final Answer:
"""

    def _filter_by_similarity(self, relevant_docs: List[Dict]) -> List[Dict]:
        """Filter docs based on similarity threshold"""
        return [doc for doc in relevant_docs if doc["score"] >= self.min_similarity_threshold]

    def _calculate_confidence(self, relevant_docs: List[Dict], answer: str) -> float:
        """Confidence = weighted similarity + linguistic coherence score"""
        if not relevant_docs:
            return 0.0

        # Weighted average of similarity scores
        scores = [doc["score"] for doc in relevant_docs]
        weights = [1.0, 0.8, 0.6, 0.4, 0.2][: len(scores)]
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        # Simple coherence heuristic (based on answer length + structure)
        coherence_score = min(len(re.findall(r"[.!?]", answer)) / 5, 1.0)
        final_conf = round(min(weighted_score * 0.7 + coherence_score * 0.3, 1.0), 2)

        return final_conf

    async def _expand_query(self, query: str) -> str:
        """LLM-assisted query expansion for better retrieval"""
        try:
            prompt = f"Generate a few related terms and synonyms for this query: '{query}'. Keep it concise."

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You improve search coverage by adding relevant terms."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=80,
                temperature=0.4,
            )

            expanded = response.choices[0].message.content.strip()
            logger.info(f"🔍 Query expanded: {query} → {expanded}")
            return expanded

        except Exception as e:
            logger.warning(f"Query expansion failed: {str(e)}")
            return query

    async def generate_summary(self, documents: List[Dict]) -> str:
        """Summarize multiple documents"""
        try:
            context = self._prepare_context(documents)
            prompt = f"Summarize the following documents concisely:\n\n{context}\n\nSummary:"

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You summarize content precisely and factually."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.5,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"

    async def extract_keywords(self, query: str) -> List[str]:
        """Extract essential keywords from a user query"""
        try:
            prompt = f"Extract 3-6 important keywords or key phrases from this query:\n\n'{query}'"

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract concise and relevant keywords."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=80,
                temperature=0.3,
            )

            keywords_text = response.choices[0].message.content.strip()
            return [kw.strip() for kw in re.split(r",|;|\n", keywords_text) if kw.strip()]

        except Exception as e:
            logger.warning(f"Keyword extraction failed: {str(e)}")
            return [query]

    # ============================================================
    # 🧪 NEW: Evaluation Function for Synthesis Quality
    # ============================================================
    async def evaluate_synthesis_quality(self, ground_truth: str, generated_answer: str) -> float:
        """
        Use the model to self-evaluate the quality of its generated answer.
        Returns a score between 0.0 and 1.0.
        """
        try:
            eval_prompt = f"""
You are an evaluator grading an answer's quality.

Question Reference:
{ground_truth}

Model Answer:
{generated_answer}

Evaluate coherence, factuality, and completeness on a scale of 0 to 10.
Return only the numeric score.
"""
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an impartial evaluator."},
                    {"role": "user", "content": eval_prompt},
                ],
                max_tokens=10,
                temperature=0.0,
            )

            score_text = response.choices[0].message.content.strip()
            match = re.search(r"\d+(\.\d+)?", score_text)
            score = float(match.group()) / 10 if match else 0.0
            return round(min(max(score, 0.0), 1.0), 2)

        except Exception as e:
            logger.warning(f"Synthesis evaluation failed: {str(e)}")
            return 0.0

