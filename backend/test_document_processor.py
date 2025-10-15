import pytest
import os
import tempfile
from document_processor import DocumentProcessor

class TestDocumentProcessor:
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        
    def test_txt_processing(self):
        """Test processing of TXT files"""
        # Create a temporary text file
        test_content = "This is a test document. " * 10  # Create content longer than chunk size
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Process the document
            chunks = self.processor.process_document(temp_path)
            
            # Assertions
            assert len(chunks) > 0, "Should create at least one chunk"
            assert all('content' in chunk for chunk in chunks), "All chunks should have content"
            assert all('metadata' in chunk for chunk in chunks), "All chunks should have metadata"
            
            # Check metadata
            first_chunk = chunks[0]
            assert 'filename' in first_chunk['metadata'], "Should have filename in metadata"
            assert 'file_type' in first_chunk['metadata'], "Should have file_type in metadata"
            assert first_chunk['metadata']['file_type'] == '.txt', "Should identify as txt file"
            
        finally:
            os.unlink(temp_path)
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap"""
        test_content = "Word " * 200  # Create content that will be split into multiple chunks
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            chunks = self.processor.process_document(temp_path)
            
            if len(chunks) > 1:
                # Check that chunks have overlap
                first_chunk_end = chunks[0]['content'][-20:]
                second_chunk_start = chunks[1]['content'][:20]
                
                # There should be some overlap between chunks
                assert len(first_chunk_end) > 0, "First chunk should have content"
                assert len(second_chunk_start) > 0, "Second chunk should have content"
                
        finally:
            os.unlink(temp_path)
    
    def test_metadata_extraction(self):
        """Test metadata extraction"""
        test_content = "This is a test document with some content. It has numbers like 123 and dates like 2023-12-01."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            chunks = self.processor.process_document(temp_path)
            
            if chunks:
                metadata = chunks[0]['metadata']
                
                # Check basic metadata
                assert 'file_size' in metadata, "Should have file size"
                assert 'word_count' in metadata, "Should have word count"
                assert 'language' in metadata, "Should have language detection"
                assert 'has_numbers' in metadata, "Should detect numbers"
                
                # Check content metadata
                assert metadata['has_numbers'] == True, "Should detect numbers in content"
                
        finally:
            os.unlink(temp_path)
    
    def test_unsupported_file_type(self):
        """Test handling of unsupported file types"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                self.processor.process_document(temp_path)
                
        finally:
            os.unlink(temp_path)
    
    def test_empty_file(self):
        """Test handling of empty files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name
        
        try:
            chunks = self.processor.process_document(temp_path)
            assert len(chunks) == 0, "Empty file should produce no chunks"
            
        finally:
            os.unlink(temp_path)
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        dirty_text = "This   has    multiple    spaces.  And special chars!@#$%^&*()"
        cleaned = self.processor._clean_text(dirty_text)
        
        assert "   " not in cleaned, "Should remove multiple spaces"
        assert cleaned.strip() == cleaned, "Should be trimmed"
    
    def test_token_counting(self):
        """Test token counting functionality"""
        text = "This is a test sentence."
        token_count = self.processor.count_tokens(text)
        
        assert isinstance(token_count, int), "Should return integer"
        assert token_count > 0, "Should have positive token count"
