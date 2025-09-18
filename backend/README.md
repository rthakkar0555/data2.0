# Backend API - Vercel Deployment

This FastAPI backend is configured for deployment on Vercel.

## Environment Variables

Before deploying, make sure to set the following environment variables in your Vercel dashboard:

### MongoDB Configuration
- `MONGODB_URI` - Your MongoDB connection string (e.g., mongodb+srv://user:pass@cluster.mongodb.net/)
- `MONGODB_DB` - Your database name
- `MONGODB_COLLECTION` - Your collection name

### JWT Secret Key
- `SECRET_KEY` - Your JWT secret key (change from default)

### Cloudinary Configuration
- `CLOUDINARY_CLOUD_NAME` - Your Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Your Cloudinary API key
- `CLOUDINARY_API_SECRET` - Your Cloudinary API secret

### Qdrant Configuration
- `QDRANT_URL` - Your Qdrant URL
- `QDRANT_API_KEY` - Your Qdrant API key
- `QDRANT_COLLECTION_NAME` - Your collection name

### NVIDIA NIM Configuration
- `NVIDIA_API_KEY` - Your NVIDIA API key
- `NVIDIA_BASE_URL` - https://integrate.api.nvidia.com/v1
- `NVIDIA_EMBEDDING_MODEL` - nvidia/nv-embed-v1
- `NVIDIA_CHAT_MODEL` - nvidia/llama-3.1-nemotron-70b-instruct

### Default Admin User (for development)
- `DEFAULT_ADMIN_EMAIL` - admin@manualbase.com
- `DEFAULT_ADMIN_PASSWORD` - admin123

## Deployment Steps

1. **Connect to Vercel**: Link your GitHub repository to Vercel
2. **Set Environment Variables**: Add all the above environment variables in Vercel dashboard
3. **Deploy**: Vercel will automatically build and deploy your FastAPI app

## API Endpoints

Once deployed, your API will be available at:
- `https://your-app-name.vercel.app/`
- Health check: `https://your-app-name.vercel.app/health/`
- Upload PDF: `https://your-app-name.vercel.app/upload_pdf/`
- Chat query: `https://your-app-name.vercel.app/query/`

## Local Development

To run locally:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## File Structure

```
backend/
├── api/
│   └── index.py          # Vercel entry point
├── main.py               # Main FastAPI app
├── auth.py               # Authentication routes
├── chat.py               # Chat/query routes
├── nvidia_embeddings.py  # NVIDIA embeddings
├── diagnostic.py         # Diagnostic tools
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (local only)
```