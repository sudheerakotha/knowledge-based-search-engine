Knowledge Base Search Engine
A modern, production-ready RAG (Retrieval-Augmented Generation) system for intelligent document search and Q&A.

🎯 Overview
This project enables users to upload documents (PDF, DOCX, TXT) and query them using advanced AI techniques. It combines semantic search, metadata filtering, and synthesis through large language models to deliver accurate, context-aware answers.

🚀 Key Features
Document Upload: PDF, DOCX, and TXT support with intelligent chunking for efficient processing

Semantic Search: Fast, vector-based similarity search via ChromaDB and sentence-transformers

Answer Generation: OpenAI GPT-3.5-turbo for synthesized, source-attributed responses

Advanced Filters: Query by document type, language, source, and date ranges

Metadata Extraction: Topics, entities, dates, emails, and more

Modern Frontend: Responsive React + Tailwind UI with document management, search, export, filters

Testing & QA: Comprehensive backend and frontend test coverage

🏗️ Tech Stack
Backend: FastAPI, ChromaDB, Sentence Transformers, OpenAI API (GPT-3.5), PyPDF2, python-docx, Pydantic

Frontend: React, Tailwind CSS, Axios, React Markdown, Lucide React

📦 Project Structure
text
knowledge-based-search-engine/
├── backend/            # FastAPI backend, vector store, RAG pipeline, tests
├── frontend/           # React frontend app, UI components, styles
├── uploads/            # Temporary file storage
├── requirements.txt    # Python dependencies
├── PROJECT_SUMMARY.md  # Technical/project overview
├── SETUP_GUIDE.md      # Installation and configuration instructions
📝 Setup Instructions
Prerequisites
Python 3.8+

Node.js 16+

OpenAI API key

Git

1. Clone & Backend Setup
bash
git clone https://github.com/sudheerakotha/knowledge-based-search-engine.git
cd knowledge-based-search-engine
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # Set your OPENAI_API_KEY in .env
python run_backend.py  # Or: cd backend && python main.py
Backend API runs at http://localhost:8000

2. Frontend Setup
bash
cd frontend
npm install
python run_frontend.py  # Or npm start
Frontend runs at http://localhost:3000

🗂️ Usage
Upload supported documents via UI or API

Ask questions using semantic search and LLM synthesis

Filter results by file type, language, dates, and source

Export answers and view document/query history

Access API documentation at /docs (Swagger UI)

🧪 Testing
Backend: cd backend && pytest

Frontend: cd frontend && npm test

⚙️ Configuration
Environment variables (.env):

OPENAI_API_KEY: Your OpenAI token

CHROMA_PERSIST_DIRECTORY: Directory for vector database

Other customizable parameters: chunk size, LLM settings, thresholds, UI config

📄 Documentation
For detailed setup and technical details, see:

PROJECT_SUMMARY.md

SETUP_GUIDE.md

🤝 Contributing
Fork the repo, create a feature branch, add tests, and submit a pull request

🛠️ Troubleshooting
API key/config issues: check .env and API credits

Upload errors: file formats and size limits

Vector store: reset by clearing chroma_db

Frontend: verify backend connection and CORS

More: see SETUP_GUIDE.md
