import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from rag_engine import RAGEngine

class TestRAGEngine:
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the OpenAI client
        with patch('rag_engine.AsyncOpenAI'):
            self.rag_engine = RAGEngine()
            self.rag_engine.client = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_generate_answer_success(self):
        """Test successful answer generation"""
        # Mock relevant documents
        relevant_docs = [
            {
                "content": "Machine learning is a subset of AI",
                "metadata": {"source": "test_doc.pdf"},
                "score": 0.9
            },
            {
                "content": "Deep learning uses neural networks",
                "metadata": {"source": "test_doc2.pdf"},
                "score": 0.8
            }
        ]
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Machine learning is a subset of artificial intelligence that focuses on algorithms."
        
        self.rag_engine.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Test
        query = "What is machine learning?"
        answer, confidence = await self.rag_engine.generate_answer(query, relevant_docs)
        
        # Assertions
        assert isinstance(answer, str), "Should return string answer"
        assert isinstance(confidence, float), "Should return float confidence"
        assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
        assert len(answer) > 0, "Answer should not be empty"
        
        # Verify OpenAI was called
        self.rag_engine.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_answer_no_documents(self):
        """Test answer generation with no relevant documents"""
        relevant_docs = []
        
        answer, confidence = await self.rag_engine.generate_answer("test query", relevant_docs)
        
        assert "No relevant documents" in answer or "couldn't find" in answer.lower()
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_generate_answer_low_similarity(self):
        """Test answer generation with low similarity documents"""
        relevant_docs = [
            {
                "content": "Unrelated content",
                "metadata": {"source": "test_doc.pdf"},
                "score": 0.1  # Below threshold
            }
        ]
        
        answer, confidence = await self.rag_engine.generate_answer("test query", relevant_docs)
        
        assert "couldn't find relevant information" in answer.lower()
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_generate_answer_openai_error(self):
        """Test handling of OpenAI API errors"""
        relevant_docs = [
            {
                "content": "Test content",
                "metadata": {"source": "test_doc.pdf"},
                "score": 0.9
            }
        ]
        
        # Mock OpenAI error
        self.rag_engine.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        answer, confidence = await self.rag_engine.generate_answer("test query", relevant_docs)
        
        assert "Error generating answer" in answer
        assert confidence == 0.0
    
    def test_prepare_context(self):
        """Test context preparation from documents"""
        relevant_docs = [
            {
                "content": "First document content",
                "metadata": {"source": "doc1.pdf"},
                "score": 0.9
            },
            {
                "content": "Second document content",
                "metadata": {"source": "doc2.pdf"},
                "score": 0.8
            }
        ]
        
        context = self.rag_engine._prepare_context(relevant_docs)
        
        assert "First document content" in context
        assert "Second document content" in context
        assert "doc1.pdf" in context
        assert "doc2.pdf" in context
        assert "0.90" in context  # Score formatting
        assert "0.80" in context
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # Test with high scores
        high_score_docs = [
            {"score": 0.9},
            {"score": 0.8},
            {"score": 0.7}
        ]
        
        confidence = self.rag_engine._calculate_confidence(high_score_docs)
        assert confidence > 0.8, "High scores should result in high confidence"
        
        # Test with low scores
        low_score_docs = [
            {"score": 0.3},
            {"score": 0.2}
        ]
        
        confidence = self.rag_engine._calculate_confidence(low_score_docs)
        assert confidence < 0.5, "Low scores should result in low confidence"
        
        # Test with no documents
        confidence = self.rag_engine._calculate_confidence([])
        assert confidence == 0.0, "No documents should result in zero confidence"
    
    def test_filter_by_similarity(self):
        """Test document filtering by similarity threshold"""
        docs = [
            {"score": 0.9, "content": "high relevance"},
            {"score": 0.5, "content": "medium relevance"},
            {"score": 0.2, "content": "low relevance"}
        ]
        
        filtered = self.rag_engine._filter_by_similarity(docs)
        
        # Should filter out low relevance documents
        assert len(filtered) == 2, "Should keep high and medium relevance docs"
        assert all(doc["score"] >= self.rag_engine.min_similarity_threshold for doc in filtered)
    
    def test_rerank_documents(self):
        """Test document reranking by keyword overlap"""
        query = "machine learning algorithms"
        docs = [
            {"content": "This is about algorithms and machine learning", "score": 0.7},
            {"content": "Random content about something else", "score": 0.9},
            {"content": "Machine learning is important for algorithms", "score": 0.6}
        ]
        
        reranked = self.rag_engine._rerank_documents(query, docs)
        
        # Should prioritize documents with keyword overlap
        assert "keyword_overlap" in reranked[0], "Should add keyword overlap score"
        assert reranked[0]["keyword_overlap"] >= reranked[-1]["keyword_overlap"], "Should be sorted by overlap"
    
    @pytest.mark.asyncio
    async def test_expand_query(self):
        """Test query expansion functionality"""
        # Mock OpenAI response for query expansion
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "machine learning algorithms artificial intelligence"
        
        self.rag_engine.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        original_query = "ML algorithms"
        expanded = await self.rag_engine._expand_query(original_query)
        
        assert isinstance(expanded, str), "Should return string"
        assert len(expanded) > len(original_query), "Expanded query should be longer"
        
        # Verify OpenAI was called for expansion
        self.rag_engine.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_expand_query_error(self):
        """Test query expansion error handling"""
        # Mock OpenAI error
        self.rag_engine.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        original_query = "test query"
        expanded = await self.rag_engine._expand_query(original_query)
        
        assert expanded == original_query, "Should return original query on error"
