import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Search, FileText, Trash2, Loader2, Filter, Settings, BarChart3, Download, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [confidence, setConfidence] = useState(0);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [uploadMessage, setUploadMessage] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({});
  const [metadata, setMetadata] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    maxResults: 5,
    temperature: 0.7,
    model: 'gpt-3.5-turbo'
  });

  useEffect(() => {
    fetchDocuments();
    fetchMetadata();
    loadQueryHistory();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`);
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleFileUpload = async (files) => {
    setUploading(true);
    setUploadMessage('');
    
    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadMessage(`Successfully processed ${response.data.processed_files.length} files with ${response.data.total_chunks} chunks`);
      fetchDocuments();
    } catch (error) {
      setUploadMessage(`Error uploading files: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setAnswer('');
    setSources([]);
    setConfidence(0);

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: query.trim(),
        max_results: 5
      });

      setAnswer(response.data.answer);
      setSources(response.data.sources);
      setConfidence(response.data.confidence);
      saveQueryHistory(query);
    } catch (error) {
      setAnswer(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (documentName) => {
    try {
      await axios.delete(`${API_BASE_URL}/documents/${encodeURIComponent(documentName)}`);
      fetchDocuments();
      fetchMetadata();
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const fetchMetadata = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents/metadata`);
      setMetadata(response.data);
    } catch (error) {
      console.error('Error fetching metadata:', error);
    }
  };

  const loadQueryHistory = () => {
    const saved = localStorage.getItem('queryHistory');
    if (saved) {
      setQueryHistory(JSON.parse(saved));
    }
  };

  const saveQueryHistory = (query) => {
    const newHistory = [query, ...queryHistory.filter(q => q !== query)].slice(0, 10);
    setQueryHistory(newHistory);
    localStorage.setItem('queryHistory', JSON.stringify(newHistory));
  };

  const handleAdvancedSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setAnswer('');
    setSources([]);
    setConfidence(0);

    try {
      const response = await axios.post(`${API_BASE_URL}/search/advanced`, {
        query: query.trim(),
        max_results: settings.maxResults,
        filters: Object.keys(filters).length > 0 ? filters : undefined
      });

      setSources(response.data.results.map(result => ({
        content: result.content.substring(0, 200) + (result.content.length > 200 ? '...' : ''),
        source: result.metadata.source,
        score: result.score
      })));
      
      saveQueryHistory(query);
    } catch (error) {
      console.error('Error in advanced search:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportResults = () => {
    if (!answer && sources.length === 0) return;
    
    const exportData = {
      query,
      answer,
      sources,
      confidence,
      timestamp: new Date().toISOString(),
      filters: Object.keys(filters).length > 0 ? filters : null
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `search-results-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <div className="flex justify-between items-center mb-4">
            <div className="flex space-x-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`px-3 py-1 rounded-md text-sm flex items-center ${
                  showFilters ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'
                }`}
              >
                <Filter size={16} className="mr-1" />
                Filters
              </button>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className={`px-3 py-1 rounded-md text-sm flex items-center ${
                  showSettings ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'
                }`}
              >
                <Settings size={16} className="mr-1" />
                Settings
              </button>
            </div>
            {metadata && (
              <div className="flex items-center text-sm text-gray-600">
                <BarChart3 size={16} className="mr-1" />
                {metadata.total_documents} docs, {metadata.total_chunks} chunks
              </div>
            )}
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Knowledge Base Search Engine
          </h1>
          <p className="text-gray-600">
            Upload documents and ask questions using RAG-powered search
          </p>
        </header>

        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Filter className="mr-2" />
              Search Filters
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">File Type</label>
                <select
                  value={filters.file_type || ''}
                  onChange={(e) => setFilters({...filters, file_type: e.target.value || undefined})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">All Types</option>
                  <option value=".pdf">PDF</option>
                  <option value=".docx">DOCX</option>
                  <option value=".txt">TXT</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                <select
                  value={filters.language || ''}
                  onChange={(e) => setFilters({...filters, language: e.target.value || undefined})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">All Languages</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Source Document</label>
                <select
                  value={filters.source || ''}
                  onChange={(e) => setFilters({...filters, source: e.target.value || undefined})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">All Documents</option>
                  {documents.map(doc => (
                    <option key={doc} value={doc}>{doc}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setFilters({})}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Clear Filters
              </button>
            </div>
          </div>
        )}

        {/* Settings Panel */}
        {showSettings && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Settings className="mr-2" />
              Search Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Results</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={settings.maxResults}
                  onChange={(e) => setSettings({...settings, maxResults: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => setSettings({...settings, temperature: parseFloat(e.target.value)})}
                  className="w-full"
                />
                <span className="text-sm text-gray-600">{settings.temperature}</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                <select
                  value={settings.model}
                  onChange={(e) => setSettings({...settings, model: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                </select>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              <Upload className="mr-2" />
              Upload Documents
            </h2>
            
            <div className="mb-4">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={(e) => handleFileUpload(e.target.files)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
            </div>

            {uploading && (
              <div className="flex items-center text-blue-600 mb-4">
                <Loader2 className="animate-spin mr-2" />
                Uploading and processing documents...
              </div>
            )}

            {uploadMessage && (
              <div className={`p-3 rounded-md mb-4 ${
                uploadMessage.includes('Error') 
                  ? 'bg-red-50 text-red-700 border border-red-200' 
                  : 'bg-green-50 text-green-700 border border-green-200'
              }`}>
                {uploadMessage}
              </div>
            )}

            {/* Document List */}
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-3">Uploaded Documents</h3>
              {documents.length === 0 ? (
                <p className="text-gray-500 text-sm">No documents uploaded yet</p>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div className="flex items-center">
                        <FileText className="mr-2 text-gray-500" size={16} />
                        <span className="text-sm font-medium">{doc}</span>
                      </div>
                      <button
                        onClick={() => deleteDocument(doc)}
                        className="text-red-500 hover:text-red-700 p-1"
                        title="Delete document"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Query Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              <Search className="mr-2" />
              Ask Questions
            </h2>

            <form onSubmit={handleQuery} className="mb-6">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about your documents..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={loading}
                  list="query-history"
                />
                <datalist id="query-history">
                  {queryHistory.map((q, index) => (
                    <option key={index} value={q} />
                  ))}
                </datalist>
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <Loader2 className="animate-spin" size={20} />
                  ) : (
                    <Search size={20} />
                  )}
                </button>
              </div>
            </form>

            {/* Advanced Search Options */}
            <div className="mb-6 flex gap-2">
              <button
                onClick={handleAdvancedSearch}
                disabled={loading || !query.trim()}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <Filter size={16} className="mr-1" />
                Advanced Search
              </button>
              {(answer || sources.length > 0) && (
                <button
                  onClick={exportResults}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 flex items-center"
                >
                  <Download size={16} className="mr-1" />
                  Export
                </button>
              )}
            </div>

            {/* Query History */}
            {queryHistory.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Queries</h4>
                <div className="flex flex-wrap gap-2">
                  {queryHistory.slice(0, 5).map((q, index) => (
                    <button
                      key={index}
                      onClick={() => setQuery(q)}
                      className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
                    >
                      {q.length > 30 ? q.substring(0, 30) + '...' : q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Answer Section */}
            {answer && (
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                  <h3 className="font-medium text-blue-900 mb-2">Answer</h3>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{answer}</ReactMarkdown>
                  </div>
                  {confidence > 0 && (
                    <div className="mt-3 text-sm text-blue-700">
                      Confidence: {(confidence * 100).toFixed(1)}%
                    </div>
                  )}
                </div>

                {/* Sources */}
                {sources.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Sources</h3>
                    <div className="space-y-2">
                      {sources.map((source, index) => (
                        <div key={index} className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">
                              {source.source}
                            </span>
                            <span className="text-xs text-gray-500">
                              Relevance: {(source.score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{source.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;


