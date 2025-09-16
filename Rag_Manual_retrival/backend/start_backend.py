#!/usr/bin/env python3
"""
Backend startup script with environment validation
"""
import os
import sys
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for embeddings and chat',
        'MONGODB_URI': 'MongoDB connection string'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var}: {description}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 To fix this:")
        print("1. Create a .env file in the backend directory")
        print("2. Add the following variables:")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        print("   MONGODB_URI=mongodb+srv://rishi:rishi123@cluster0.1tfj3.mongodb.net/datquest")
        print("   MONGODB_DB=datquest")
        print("   MONGODB_COLLECTION=uploads")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import langchain
        import openai
        import pymongo
        import qdrant_client
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_qdrant():
    """Check if Qdrant is running"""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://localhost:6333")
        client.get_collections()
        print("✅ Qdrant is running")
        return True
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        print("💡 Start Qdrant with: docker-compose up -d")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Manual Retrieval Backend...")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Qdrant
    if not check_qdrant():
        print("⚠️  Qdrant not available, but continuing...")
    
    print("=" * 50)
    print("✅ All checks passed! Starting server...")
    
    # Start the server
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
