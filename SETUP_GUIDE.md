# Knowledge Base Search Engine - Setup Guide

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd knowledge-base-search
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENROUTER_API_KEY=your_openai_api_key_here
```

#### Run Backend
```bash
# Option 1: Using the run script
python run_backend.py

# Option 2: Direct execution
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Start Development Server
```bash
# Option 1: Using the run script
python run_frontend.py

# Option 2: Direct execution
npm start
```

The frontend will be available at `http://localhost:3000`

## Detailed Setup Instructions

### Backend Configuration

#### Environment Variables
Create a `.env` file in the root directory with the following variables:

```env
# OpenAI API Configuration
OPENROUTER_API_KEY=your_openai_api_key_here

# Vector Store Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Application Configuration
APP_NAME=Knowledge Base Search Engine
APP_VERSION=1.0.0
DEBUG=True

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Document Processing Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=50

# LLM Configuration
LLM_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7

# Search Configuration
MAX_SEARCH_RESULTS=5
MIN_SIMILARITY_THRESHOLD=0.3

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
```

#### Dependencies
The backend uses the following key dependencies:

- **FastAPI**: Web framework for building APIs
- **ChromaDB**: Vector database for similarity search
- **Sentence Transformers**: Text embeddings
- **OpenAI**: GPT-3.5-turbo for answer generation
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX text extraction

### Frontend Configuration

#### Dependencies
The frontend uses the following key dependencies:

- **React**: UI library
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client
- **React Markdown**: Markdown rendering
- **Lucide React**: Icons

#### Customization
You can customize the frontend by modifying:

- `src/App.js`: Main application component
- `src/index.css`: Global styles
- `tailwind.config.js`: Tailwind configuration
- `package.json`: Dependencies and scripts

### Database Setup

#### ChromaDB
ChromaDB is automatically initialized when the backend starts. The database files are stored in the `chroma_db` directory.

#### Reset Database
To reset the vector database:
```bash
rm -rf chroma_db/
# Restart the backend
```

### Testing

#### Backend Tests
```bash
cd backend
pytest
```

#### Frontend Tests
```bash
cd frontend
npm test
```

### Production Deployment

#### Backend Deployment
1. Set up a production environment
2. Configure environment variables
3. Use a production WSGI server like Gunicorn
4. Set up reverse proxy with Nginx

#### Frontend Deployment
1. Build the production bundle:
   ```bash
   cd frontend
   npm run build
   ```
2. Serve the `build` directory with a web server
3. Configure API endpoints for production

### Troubleshooting

#### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is correctly set in `.env`
   - Check if you have sufficient API credits
   - Verify the key has the correct permissions

2. **Document Upload Fails**
   - Verify file format is supported (PDF, DOCX, TXT)
   - Check file size and corruption
   - Ensure sufficient disk space

3. **Vector Store Issues**
   - Delete `chroma_db` folder to reset the database
   - Check ChromaDB installation
   - Verify sufficient disk space

4. **Frontend Connection Issues**
   - Verify backend is running on port 8000
   - Check CORS settings
   - Ensure no firewall blocking

5. **Memory Issues**
   - Reduce chunk size in configuration
   - Limit number of concurrent uploads
   - Monitor system resources

#### Logs
- Backend logs: `knowledge_base.log`
- Console logs: Check browser developer tools
- System logs: Check system logs for resource issues

### Performance Optimization

#### Backend Optimization
- Use production WSGI server
- Enable response compression
- Implement caching
- Optimize database queries

#### Frontend Optimization
- Enable code splitting
- Use CDN for static assets
- Implement lazy loading
- Optimize bundle size

### Security Considerations

#### API Security
- Implement authentication/authorization
- Use HTTPS in production
- Validate input data
- Rate limiting

#### Data Security
- Encrypt sensitive data
- Secure file uploads
- Regular security updates
- Access control

### Monitoring and Maintenance

#### Health Checks
- Use `/health` endpoint for monitoring
- Set up automated health checks
- Monitor API response times
- Track error rates

#### Backup Strategy
- Regular database backups
- Document storage backup
- Configuration backup
- Disaster recovery plan

### Development Workflow

#### Code Organization
```
knowledge-base-search/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── document_processor.py # Document processing
│   ├── vector_store.py      # Vector database
│   ├── rag_engine.py        # RAG implementation
│   └── test_*.py           # Unit tests
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main component
│   │   ├── index.js        # Entry point
│   │   └── index.css       # Styles
│   └── package.json        # Dependencies
├── docs/                   # Documentation
├── uploads/                # Temporary files
└── requirements.txt        # Python dependencies
```

#### Git Workflow
1. Create feature branches
2. Write tests for new features
3. Ensure all tests pass
4. Submit pull requests
5. Code review process

### Support and Contributing

#### Getting Help
- Check the troubleshooting section
- Review API documentation at `/docs`
- Create issues on GitHub
- Check existing issues

#### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

This setup guide provides comprehensive instructions for getting the Knowledge Base Search Engine up and running in various environments.

