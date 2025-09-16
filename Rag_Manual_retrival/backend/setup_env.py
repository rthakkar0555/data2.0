#!/usr/bin/env python3
"""
Environment setup script for Manual Retrieval Backend
"""
import os
from pathlib import Path

def create_env_file():
    """Create .env file with default values"""
    env_path = Path(__file__).parent / ".env"
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Configuration
MONGODB_URI=mongodb+srv://rishi:rishi123@cluster0.1tfj3.mongodb.net/datquest
MONGODB_DB=datquest
MONGODB_COLLECTION=uploads

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=learn_vector2
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default values")
        print("⚠️  Please update OPENAI_API_KEY with your actual API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Setting up Manual Retrieval Backend environment...")
    print("=" * 50)
    
    if create_env_file():
        print("\n📝 Next steps:")
        print("1. Edit the .env file and add your OpenAI API key")
        print("2. Make sure Qdrant is running: docker-compose up -d")
        print("3. Start the backend: python start_backend.py")
    else:
        print("❌ Setup failed")

if __name__ == "__main__":
    main()
