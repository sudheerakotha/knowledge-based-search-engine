# Knowledge Base Search Engine

A powerful RAG (Retrieval-Augmented Generation) based search engine that allows you to upload documents and ask questions to get synthesized answers from your knowledge base.

## Features

- **Document Upload**: Support for PDF, DOCX, and TXT files
- **Intelligent Chunking**: Automatic text segmentation with overlap for better context
- **Vector Search**: Semantic similarity search using sentence transformers
- **RAG Integration**: OpenAI GPT-3.5-turbo for answer synthesis
- **Modern UI**: React-based frontend with Tailwind CSS
- **Real-time Processing**: Fast document ingestion and query processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Vector Store  │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (ChromaDB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   LLM Service   │
                       │   (OpenAI)      │
                       └─────────────────┘
```

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **ChromaDB**: Vector database for similarity search
- **Sentence Transformers**: Text embeddings using all-MiniLM-L6-v2
- **OpenAI API**: GPT-3.5-turbo for answer generation
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX text extraction

### Frontend
- **React**: Modern UI library
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls
- **React Markdown**: Markdown rendering for answers
- **Lucide React**: Beautiful icons

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd knowledge-base-search
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   CHROMA_PERSIST_DIRECTORY=./chroma_db
   ```

5. **Run the backend**
   ```bash
   cd backend
   python main.py
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

   The frontend will be available at `http://localhost:3000`

## Usage

### 1. Upload Documents
- Navigate to the upload section
- Select PDF, DOCX, or TXT files
- Files are automatically processed and chunked
- Documents are stored in the vector database

### 2. Ask Questions
- Type your question in the search box
- The system will:
  - Find relevant document chunks using semantic search
  - Generate a synthesized answer using the RAG pipeline
  - Display sources and confidence scores

### 3. Manage Documents
- View all uploaded documents
- Delete documents as needed
- Monitor processing status

## API Endpoints

### Document Management
- `POST /upload` - Upload and process documents
- `GET /documents` - List all documents
- `DELETE /documents/{name}` - Delete a specific document

### Query
- `POST /query` - Query the knowledge base
  ```json
  {
    "query": "What is machine learning?",
    "max_results": 5
  }
  ```

### Health Check
- `GET /health` - Check system status

## Configuration

### Document Processing
- **Chunk Size**: 1000 tokens (configurable in `document_processor.py`)
- **Chunk Overlap**: 200 tokens
- **Supported Formats**: PDF, DOCX, TXT

### Vector Search
- **Embedding Model**: all-MiniLM-L6-v2
- **Similarity Metric**: Cosine similarity
- **Max Results**: 5 (configurable)

### LLM Settings
- **Model**: GPT-3.5-turbo
- **Max Tokens**: 1000
- **Temperature**: 0.7

## Example Queries

- "What are the main topics discussed in the documents?"
- "Summarize the key findings from the research papers"
- "What are the best practices mentioned in the documentation?"
- "Explain the methodology used in the study"

## Performance Considerations

- **Document Size**: Large documents are automatically chunked
- **Processing Time**: Initial upload may take time for large files
- **Memory Usage**: Vector embeddings are stored in ChromaDB
- **API Limits**: Respect OpenAI API rate limits

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is correctly set in `.env`
   - Check if you have sufficient API credits

2. **Document Upload Fails**
   - Verify file format is supported (PDF, DOCX, TXT)
   - Check file size and corruption

3. **Vector Store Issues**
   - Delete `chroma_db` folder to reset the database
   - Ensure sufficient disk space

4. **Frontend Connection Issues**
   - Verify backend is running on port 8000
   - Check CORS settings if running on different ports

## Development

### Project Structure
```
knowledge-base-search/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── document_processor.py # Document parsing and chunking
│   ├── vector_store.py      # ChromaDB integration
│   └── rag_engine.py        # RAG pipeline
├── frontend/
│   ├── src/
│   │   ├── App.js           # Main React component
│   │   ├── index.js         # React entry point
│   │   └── index.css        # Tailwind CSS
│   └── package.json         # Frontend dependencies
├── docs/                    # Sample documents
├── uploads/                 # Temporary file storage
└── requirements.txt         # Python dependencies
```

### Adding New Features

1. **New Document Types**: Extend `DocumentProcessor` class
2. **Different Embeddings**: Modify `VectorStore` initialization
3. **Custom LLM**: Update `RAGEngine` with different models
4. **UI Enhancements**: Modify React components in `frontend/src`


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Demo Video

(https://drive.google.com/file/d/1vQ1vgOlNQimXYDGzyB9xw_aAKdEWT6-l/view?usp=sharing)

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section
- Review the API documentation

---

Built with ❤️ using FastAPI, React, and OpenAI


# knowledge-based-search-engine
