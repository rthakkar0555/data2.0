# Manual Retrieval Backend

A FastAPI-based backend service for document processing and retrieval using RAG (Retrieval-Augmented Generation).

## Features

- PDF document upload and processing
- Text chunking and embedding generation
- Vector storage with Qdrant
- MongoDB integration for metadata storage
- OpenAI GPT-4 integration for intelligent responses
- Company and product-based document organization

## Prerequisites

- Python 3.8+
- Docker (for Qdrant vector database)
- OpenAI API key
- MongoDB Atlas account (or local MongoDB)

## Quick Start

### 1. Environment Setup

```bash
# Run the setup script
python setup_env.py

# Edit the .env file and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Services

#### Option A: With Docker (Recommended)
```bash
# Start Qdrant vector database
docker-compose up -d

# Start the backend
python start_backend.py
```

#### Option B: Without Docker
```bash
# Start the backend (limited functionality)
python start_backend_no_docker.py
```

### 4. Access the API

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health/

## API Endpoints

### Document Management
- `POST /upload_pdf/` - Upload and process PDF documents
- `GET /get_uploaded_files/` - List uploaded files
- `POST /remove_file/` - Remove uploaded files

### Company Management
- `GET /companies/` - List all companies
- `GET /companies/current/` - Get current company
- `GET /companies/{company}/models/` - List models for a company

### Chat/Query
- `POST /query/` - Process queries with RAG
- `GET /health/` - Health check endpoint

## Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/database

# Optional
MONGODB_DB=datquest
MONGODB_COLLECTION=uploads
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=learn_vector2
```

### MongoDB Setup

The backend uses MongoDB Atlas by default. To use a local MongoDB:

```env
MONGODB_URI=mongodb://localhost:27017/datquest
```

## Troubleshooting

### Common Issues

1. **Internal Server Error**
   - Check if OpenAI API key is set
   - Verify MongoDB connection
   - Ensure Qdrant is running (if using vector search)

2. **Qdrant Connection Failed**
   - Start Docker Desktop
   - Run `docker-compose up -d`
   - Check if port 6333 is available

3. **MongoDB Connection Failed**
   - Verify MongoDB URI in .env file
   - Check network connectivity
   - Ensure MongoDB Atlas IP whitelist includes your IP

### Health Check

Visit http://localhost:8000/health/ to verify all services are running properly.

## Development

### Project Structure

```
backend/
├── main.py              # Main FastAPI application
├── chat.py              # Chat/query endpoints
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Qdrant service definition
├── start_backend.py     # Startup script with checks
├── setup_env.py         # Environment setup
└── README.md           # This file
```

### Adding New Features

1. Create new endpoints in `main.py` or separate router files
2. Add error handling for external service failures
3. Update health check endpoint if needed
4. Test with both Docker and non-Docker setups

## Production Deployment

For production deployment:

1. Set `allow_origins` in CORS middleware to specific domains
2. Use environment-specific MongoDB and Qdrant instances
3. Implement proper logging and monitoring
4. Add authentication and authorization
5. Use a production WSGI server like Gunicorn

## Support

For issues and questions:
1. Check the health endpoint first
2. Review logs for error details
3. Verify all environment variables are set
4. Ensure all external services are running
