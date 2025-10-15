import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app

class TestMainAPI:
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
        
        # Mock the components
        self.mock_vector_store = AsyncMock()
        self.mock_document_processor = AsyncMock()
        self.mock_rag_engine = AsyncMock()
    
    @patch('main.vector_store')
    @patch('main.document_processor')
    @patch('main.rag_engine')
    def test_root_endpoint(self, mock_rag, mock_processor, mock_vector):
        """Test root endpoint"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    @patch('main.vector_store')
    def test_health_check(self, mock_vector):
        """Test health check endpoint"""
        mock_vector.is_initialized = True
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["vector_store_ready"] == True
        assert "timestamp" in data
    
    @patch('main.vector_store')
    @patch('main.document_processor')
    def test_upload_documents_success(self, mock_processor, mock_vector):
        """Test successful document upload"""
        # Mock the components
        mock_vector.is_initialized = True
        mock_processor.process_document.return_value = [
            {"content": "Test content", "metadata": {"chunk_index": 0}}
        ]
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as file:
                response = self.client.post(
                    "/upload",
                    files={"files": ("test.txt", file, "text/plain")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "processed_files" in data
            assert "total_chunks" in data
            assert data["processed_files"] == ["test.txt"]
            assert data["total_chunks"] == 1
            
        finally:
            os.unlink(temp_path)
    
    @patch('main.vector_store')
    def test_upload_unsupported_file_type(self, mock_vector):
        """Test upload with unsupported file type"""
        mock_vector.is_initialized = True
        
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"Test content")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as file:
                response = self.client.post(
                    "/upload",
                    files={"files": ("test.xyz", file, "application/octet-stream")}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert "Unsupported file type" in data["detail"]
            
        finally:
            os.unlink(temp_path)
    
    @patch('main.vector_store')
    @patch('main.rag_engine')
    def test_query_success(self, mock_rag, mock_vector):
        """Test successful query"""
        # Mock the components
        mock_vector.is_initialized = True
        mock_vector.search.return_value = [
            {
                "content": "Machine learning is a subset of AI",
                "metadata": {"source": "test_doc.pdf"},
                "score": 0.9
            }
        ]
        mock_rag.generate_answer.return_value = ("ML is a subset of AI", 0.85)
        
        query_data = {
            "query": "What is machine learning?",
            "max_results": 5
        }
        
        response = self.client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "confidence" in data
        assert data["answer"] == "ML is a subset of AI"
        assert data["confidence"] == 0.85
        assert len(data["sources"]) == 1
    
    @patch('main.vector_store')
    def test_query_vector_store_not_initialized(self, mock_vector):
        """Test query when vector store is not initialized"""
        mock_vector.is_initialized = False
        
        query_data = {"query": "test query"}
        
        response = self.client.post("/query", json=query_data)
        
        assert response.status_code == 503
        data = response.json()
        assert "Vector store not initialized" in data["detail"]
    
    @patch('main.vector_store')
    def test_query_empty_query(self, mock_vector):
        """Test query with empty query string"""
        mock_vector.is_initialized = True
        
        query_data = {"query": ""}
        
        response = self.client.post("/query", json=query_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Query cannot be empty" in data["detail"]
    
    @patch('main.vector_store')
    def test_query_no_results(self, mock_vector):
        """Test query with no relevant results"""
        mock_vector.is_initialized = True
        mock_vector.search.return_value = []
        
        query_data = {"query": "nonexistent topic"}
        
        response = self.client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "No relevant documents found" in data["answer"]
        assert data["confidence"] == 0.0
        assert len(data["sources"]) == 0
    
    @patch('main.vector_store')
    def test_list_documents(self, mock_vector):
        """Test listing documents"""
        mock_vector.list_documents.return_value = ["doc1.pdf", "doc2.pdf"]
        
        response = self.client.get("/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert data["documents"] == ["doc1.pdf", "doc2.pdf"]
    
    @patch('main.vector_store')
    def test_get_documents_metadata(self, mock_vector):
        """Test getting document metadata"""
        mock_stats = {
            "total_chunks": 10,
            "total_documents": 2,
            "documents": ["doc1.pdf", "doc2.pdf"]
        }
        mock_vector.get_collection_stats.return_value = mock_stats
        
        response = self.client.get("/documents/metadata")
        
        assert response.status_code == 200
        data = response.json()
        assert data == mock_stats
    
    @patch('main.vector_store')
    def test_advanced_search(self, mock_vector):
        """Test advanced search endpoint"""
        mock_vector.is_initialized = True
        mock_results = [
            {
                "content": "Search result content",
                "metadata": {"source": "test_doc.pdf"},
                "score": 0.8
            }
        ]
        mock_vector.search.return_value = mock_results
        
        search_data = {
            "query": "test search",
            "max_results": 5,
            "filters": {"file_type": ".pdf"}
        }
        
        response = self.client.post("/search/advanced", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert data["query"] == "test search"
        assert data["total_results"] == 1
        assert len(data["results"]) == 1
    
    @patch('main.vector_store')
    def test_delete_document_success(self, mock_vector):
        """Test successful document deletion"""
        mock_vector.delete_document.return_value = True
        
        response = self.client.delete("/documents/test_doc.pdf")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
    
    @patch('main.vector_store')
    def test_delete_document_not_found(self, mock_vector):
        """Test deleting non-existent document"""
        mock_vector.delete_document.return_value = False
        
        response = self.client.delete("/documents/nonexistent.pdf")
        
        assert response.status_code == 404
        data = response.json()
        assert "Document not found" in data["detail"]
