#!/usr/bin/env python3
"""
Diagnostic script to test the batch upload functionality
"""

import sys
import traceback

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except Exception as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import nvidia_embeddings
        print("✅ NVIDIA embeddings imported successfully")
    except Exception as e:
        print(f"❌ NVIDIA embeddings import failed: {e}")
        return False
    
    try:
        import main
        print("✅ Main module imported successfully")
    except Exception as e:
        print(f"❌ Main module import failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_embeddings():
    """Test NVIDIA embeddings functionality"""
    print("\n🔍 Testing NVIDIA embeddings...")
    
    try:
        from nvidia_embeddings import NVIDIANIMEmbeddings
        embedding_model = NVIDIANIMEmbeddings()
        
        # Test single embedding
        test_text = "This is a test document for embedding."
        embedding = embedding_model.embed_query(test_text)
        print(f"✅ Single embedding successful, dimension: {len(embedding)}")
        
        # Test batch embedding
        test_texts = [f"Test document {i}" for i in range(5)]
        embeddings = embedding_model.embed_documents(test_texts)
        print(f"✅ Batch embedding successful, processed {len(embeddings)} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        traceback.print_exc()
        return False

def test_qdrant_connection():
    """Test Qdrant connection"""
    print("\n🔍 Testing Qdrant connection...")
    
    try:
        from qdrant_client import QdrantClient
        
        qdrant_client = QdrantClient(
            url="https://c475058e-3b7d-4e3b-9251-c57de1708cb1.eu-west-2-0.aws.cloud.qdrant.io:6333",
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lm1RZR5M1o9mplR0W0WJXHH_opdKpKEvkm5LxRO5waM"
        )
        
        collections = qdrant_client.get_collections()
        print(f"✅ Qdrant connection successful, found {len(collections.collections)} collections")
        
        # Check if our collection exists
        collection_exists = any(col.name == 'learn_vector3' for col in collections.collections)
        print(f"✅ Collection 'learn_vector3' exists: {collection_exists}")
        
        return True
        
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    print("\n🔍 Testing FastAPI app creation...")
    
    try:
        from main import app
        print("✅ FastAPI app created successfully")
        
        # Check if routes are registered
        routes = [route.path for route in app.routes]
        print(f"✅ Found {len(routes)} routes")
        
        # Check for our specific routes
        expected_routes = ["/upload_pdf/", "/upload_multiple_pdfs/", "/health/"]
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} found")
            else:
                print(f"❌ Route {route} not found")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print("🚀 Starting diagnostic tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Embeddings", test_embeddings),
        ("Qdrant Connection", test_qdrant_connection),
        ("App Creation", test_app_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! The system should be working.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

