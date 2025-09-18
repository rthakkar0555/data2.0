# Vercel Deployment Guide

## Quick Deployment Steps

### 1. Prepare Your Repository
- Ensure all files are committed to your Git repository
- Make sure the `backend/` folder contains all necessary files

### 2. Connect to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Sign in with your GitHub account
3. Click "New Project"
4. Import your repository
5. Set the **Root Directory** to `backend`

### 3. Configure Environment Variables
In the Vercel dashboard, go to Settings → Environment Variables and add:

```
MONGODB_URI=mongodb+srv://rishi:rishi123@cluster0.1tfj3.mongodb.net/datquest
MONGODB_DB=datquest
MONGODB_COLLECTION=uploads
SECRET_KEY=your-secret-key-change-in-production
CLOUDINARY_CLOUD_NAME=rishiproject
CLOUDINARY_API_KEY=451394548967359
CLOUDINARY_API_SECRET=vQi8o9Cjypie4bHxvhrDSKdZjFs
QDRANT_URL=https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM
QDRANT_COLLECTION_NAME=learn_vector3
NVIDIA_API_KEY=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
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_EMBEDDING_MODEL=nvidia/nv-embed-v1
NVIDIA_CHAT_MODEL=nvidia/llama-3.1-nemotron-70b-instruct
DEFAULT_ADMIN_EMAIL=admin@manualbase.com
DEFAULT_ADMIN_PASSWORD=admin123
```

### 4. Deploy
- Click "Deploy"
- Wait for the build to complete
- Your API will be available at the provided URL

### 5. Test Your Deployment
Visit these endpoints to test:
- `https://your-app.vercel.app/health/` - Health check
- `https://your-app.vercel.app/docs` - API documentation

## Troubleshooting

### Common Issues:
1. **Build Failures**: Check that all dependencies are in `requirements.txt`
2. **Environment Variables**: Ensure all required env vars are set
3. **Timeout Issues**: Vercel has a 30-second timeout limit for serverless functions

### File Structure for Vercel:
```
backend/
├── api/
│   └── index.py          # Entry point
├── vercel.json           # Vercel config
├── requirements.txt      # Dependencies
├── main.py               # FastAPI app
├── auth.py               # Auth routes
├── chat.py               # Chat routes
├── nvidia_embeddings.py  # Embeddings
└── .vercelignore         # Ignore file
```
