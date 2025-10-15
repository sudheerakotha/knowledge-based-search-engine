import os
import logging
import PyPDF2
import docx
from typing import List, Dict, Optional
import tiktoken
import re
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "200"))
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    async def process_document(self, file_path: str) -> List[Dict]:
        """Process a document and return chunks with metadata"""
        try:
            logger.info(f"Processing document: {file_path}")
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Extract text based on file type
            if file_extension == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif file_extension == '.docx':
                text = self._extract_docx_text(file_path)
            elif file_extension == '.txt':
                text = self._extract_txt_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            if not text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return []
            
            # Clean and preprocess text
            text = self._clean_text(text)
            
            # Extract document metadata
            metadata = self._extract_metadata(file_path, text)
            
            # Split into chunks
            chunks = self._split_into_chunks(text, file_path, metadata)
            
            logger.info(f"Processed {file_path}: {len(chunks)} chunks, {len(text)} characters")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")
        return text
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise ValueError(f"Error reading DOCX file: {str(e)}")
        return text
    
    def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read()
        except Exception as e:
            raise ValueError(f"Error reading TXT file: {str(e)}")
        return text
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        # Remove multiple consecutive punctuation
        text = re.sub(r'([\.\,\!\?\;\:])\1+', r'\1', text)
        
        return text.strip()
    
    def _extract_metadata(self, file_path: str, text: str) -> Dict:
        """Extract metadata from document"""
        try:
            file_stats = os.stat(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            # Extract basic metadata
            metadata = {
                "filename": os.path.basename(file_path),
                "file_path": file_path,
                "file_size": file_stats.st_size,
                "file_hash": file_hash,
                "file_type": os.path.splitext(file_path)[1].lower(),
                "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "processed_at": datetime.now().isoformat(),
                "text_length": len(text),
                "word_count": len(text.split()),
                "language": self._detect_language(text)
            }
            
            # Extract content-based metadata
            metadata.update(self._extract_content_metadata(text))
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_path}: {str(e)}")
            return {
                "filename": os.path.basename(file_path),
                "file_path": file_path,
                "processed_at": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "unknown"
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on common words"""
        # Simple heuristic - can be enhanced with proper language detection
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = text.lower().split()[:100]  # Check first 100 words
        english_count = sum(1 for word in words if word in english_words)
        return "en" if english_count > 5 else "unknown"
    
    def _extract_content_metadata(self, text: str) -> Dict:
        """Extract content-based metadata"""
        try:
            # Extract potential topics/keywords
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            topics = list(set(words))[:10]  # Top 10 capitalized words
            
            # Extract potential dates
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
            dates = re.findall(date_pattern, text)
            
            # Extract potential email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            
            return {
                "topics": topics,
                "dates": dates[:5],  # Limit to 5 dates
                "emails": emails[:5],  # Limit to 5 emails
                "has_numbers": bool(re.search(r'\d', text)),
                "has_urls": bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text))
            }
        except Exception as e:
            logger.warning(f"Error extracting content metadata: {str(e)}")
            return {}
    
    def _split_into_chunks(self, text: str, source: str, metadata: Dict) -> List[Dict]:
        """Split text into overlapping chunks with enhanced metadata"""
        # Tokenize text
        tokens = self.encoding.encode(text)
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Get chunk tokens
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Skip very short chunks
            if len(chunk_text.strip()) > 50:
                chunk_metadata = {
                    **metadata,  # Include document metadata
                    "chunk_index": len(chunks),
                    "start_token": start,
                    "end_token": end,
                    "chunk_length": len(chunk_text),
                    "chunk_word_count": len(chunk_text.split())
                }
                
                chunks.append({
                    "content": chunk_text.strip(),
                    "metadata": chunk_metadata
                })
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start >= len(tokens) - self.chunk_overlap:
                break
        
        return chunks
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

