import pytest
import os
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from vector_store import VectorStore

class TestVectorStore:
    def setup_method(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.vector_store = VectorStore(persist_directory=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test vector store initialization"""
        with patch('vector_store.chromadb.PersistentClient') as mock_client, \
             patch('vector_store.SentenceTransformer') as mock_transformer:
            
            # Mock ChromaDB client
            mock_client_instance = MagicMock()
            mock_collection = MagicMock()
            mock_client_instance.get_or_create_collection.return_value = mock_collection
            mock_client.return_value = mock_client_instance
            
            # Mock SentenceTransformer
            mock_transformer_instance = MagicMock()
            mock_transformer.return_value = mock_transformer_instance
            
            # Test initialization
            await self.vector_store.initialize()
            
            # Assertions
            assert self.vector_store.is_initialized == True
            assert self.vector_store.client == mock_client_instance
            assert self.vector_store.collection == mock_collection
            assert self.vector_store.embedding_model == mock_transformer_instance
            
            # Verify ChromaDB was called correctly
            mock_client.assert_called_once()
            mock_client_instance.get_or_create_collection.assert_called_once_with(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
    
    @pytest.mark.asyncio
    async def test_initialize_error(self):
        """Test initialization error handling"""
        with patch('vector_store.chromadb.PersistentClient', side_effect=Exception("DB Error")):
            with pytest.raises(Exception, match="DB Error"):
                await self.vector_store.initialize()
            
            assert self.vector_store.is_initialized == False
    
    @pytest.mark.asyncio
    async def test_add_documents_not_initialized(self):
        """Test adding documents when not initialized"""
        chunks = [{"content": "test", "metadata": {"test": "data"}}]
        
        with pytest.raises(RuntimeError, match="Vector store not initialized"):
            await self.vector_store.add_documents(chunks, "test_doc.pdf")
    
    @pytest.mark.asyncio
    async def test_add_documents_success(self):
        """Test successful document addition"""
        # Mock initialization
        self.vector_store.is_initialized = True
        self.vector_store.collection = MagicMock()
        
        chunks = [
            {
                "content": "First chunk content",
                "metadata": {"chunk_index": 0, "source": "test_doc.pdf"}
            },
            {
                "content": "Second chunk content", 
                "metadata": {"chunk_index": 1, "source": "test_doc.pdf"}
            }
        ]
        
        await self.vector_store.add_documents(chunks, "test_doc.pdf")
        
        # Verify collection.add was called
        self.vector_store.collection.add.assert_called_once()
        
        # Check the arguments passed to add
        call_args = self.vector_store.collection.add.call_args
        documents = call_args[1]['documents']
        metadatas = call_args[1]['metadatas']
        ids = call_args[1]['ids']
        
        assert len(documents) == 2
        assert len(metadatas) == 2
        assert len(ids) == 2
        assert documents[0] == "First chunk content"
        assert documents[1] == "Second chunk content"
        assert metadatas[0]['source'] == "test_doc.pdf"
        assert ids[0] == "test_doc.pdf_0"
    
    @pytest.mark.asyncio
    async def test_search_not_initialized(self):
        """Test search when not initialized"""
        with pytest.raises(RuntimeError, match="Vector store not initialized"):
            await self.vector_store.search("test query")
    
    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search"""
        # Mock initialization
        self.vector_store.is_initialized = True
        self.vector_store.collection = MagicMock()
        
        # Mock search results
        mock_results = {
            "documents": [["Document 1 content", "Document 2 content"]],
            "metadatas": [[{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]],
            "distances": [[0.1, 0.3]]
        }
        
        self.vector_store.collection.query.return_value = mock_results
        
        results = await self.vector_store.search("test query", max_results=2)
        
        # Assertions
        assert len(results) == 2
        assert results[0]["content"] == "Document 1 content"
        assert results[0]["metadata"]["source"] == "doc1.pdf"
        assert results[0]["score"] == 0.9  # 1 - 0.1
        assert results[1]["score"] == 0.7  # 1 - 0.3
        
        # Verify collection.query was called
        self.vector_store.collection.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=2,
            where=None,
            include=["documents", "metadatas", "distances"]
        )
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Test search with filters"""
        # Mock initialization
        self.vector_store.is_initialized = True
        self.vector_store.collection = MagicMock()
        
        filters = {"file_type": ".pdf", "language": "en"}
        
        await self.vector_store.search("test query", filters=filters)
        
        # Verify where clause was built and passed
        call_args = self.vector_store.collection.query.call_args
        where_clause = call_args[1]['where']
        
        assert where_clause["file_type"] == ".pdf"
        assert where_clause["language"] == "en"
    
    def test_build_where_clause(self):
        """Test where clause building"""
        filters = {
            "file_type": ".pdf",
            "language": "en",
            "date_from": "2023-01-01",
            "date_to": "2023-12-31",
            "topics": ["AI", "ML"],
            "source": "test_doc.pdf"
        }
        
        where_clause = self.vector_store._build_where_clause(filters)
        
        assert where_clause["file_type"] == ".pdf"
        assert where_clause["language"] == "en"
        assert where_clause["created_at"]["$gte"] == "2023-01-01"
        assert where_clause["created_at"]["$lte"] == "2023-12-31"
        assert where_clause["topics"]["$in"] == ["AI", "ML"]
        assert where_clause["source"] == "test_doc.pdf"
    
    def test_build_where_clause_empty(self):
        """Test where clause building with empty filters"""
        where_clause = self.vector_store._build_where_clause({})
        assert where_clause == {}
    
    @pytest.mark.asyncio
    async def test_list_documents_not_initialized(self):
        """Test listing documents when not initialized"""
        with pytest.raises(RuntimeError, match="Vector store not initialized"):
            await self.vector_store.list_documents()
    
    @pytest.mark.asyncio
    async def test_list_documents_success(self):
        """Test successful document listing"""
        # Mock initialization
        self.vector_store.is_initialized = True
        self.vector_store.collection = MagicMock()
        
        # Mock get results
        mock_results = {
            "metadatas": [
                [{"source": "doc1.pdf"}],
                [{"source": "doc2.pdf"}],
                [{"source": "doc1.pdf"}]  # Duplicate source
            ]
        }
        
        self.vector_store.collection.get.return_value = mock_results
        
        documents = await self.vector_store.list_documents()
        
        # Should return unique document names
        assert len(documents) == 2
        assert "doc1.pdf" in documents
        assert "doc2.pdf" in documents
    
    @pytest.mark.asyncio
    async def test_delete_document_not_initialized(self):
        """Test deleting document when not initialized"""
        with pytest.raises(RuntimeError, match="Vector store not initialized"):
            await self.vector_store.delete_document("test_doc.pdf")
    
    @pytest.mark.asyncio
    async def test_delete_document_success(self):
        """Test successful document deletion"""
        # Mock initialization
        self.vector_store.is_initialized = True
        self.vector_store.collection = MagicMock()
        
        # Mock get results (documents to delete)
        mock_results = {
            "ids": ["test_doc.pdf_0", "test_doc.pdf_1", "test_doc.pdf_2"]
        }
        
        self.vector_store.collection.get.return_value = mock_results
        
        result = await self.vector_store.delete_document("test_doc.pdf")
        
        assert result == True
        self.vector_store.collection.delete.assert_called_once_with(ids=["test_doc.pdf_0", "test_doc.pdf_1", "test_doc.pdf_2"])
    
    @pytest.mark.asyncio
    async def test_delete_document_not_found(self):
        """Test deleting non-existent document"""
        # Mock initialization
        self.vector_store.is_initialized = True
        self.vector_store.collection = MagicMock()
        
        # Mock empty results
        mock_results = {"ids": []}
        self.vector_store.collection.get.return_value = mock_results
        
        result = await self.vector_store.delete_document("nonexistent.pdf")
        
        assert result == False
        self.vector_store.collection.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(self):
        """Test getting collection statistics"""
        # Mock initialization
        self.vector_store.is_initialized = True
        self.vector_store.collection = MagicMock()
        
        # Mock count and list_documents
        self.vector_store.collection.count.return_value = 10
        with patch.object(self.vector_store, 'list_documents', return_value=["doc1.pdf", "doc2.pdf"]):
            stats = await self.vector_store.get_collection_stats()
        
        assert stats["total_chunks"] == 10
        assert stats["total_documents"] == 2
        assert stats["documents"] == ["doc1.pdf", "doc2.pdf"]
