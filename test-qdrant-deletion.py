#!/usr/bin/env python3
"""
Test script to verify Qdrant deletion is working properly
"""
import requests
import json
from qdrant_client import QdrantClient
from qdrant_client.http import models

def test_qdrant_deletion():
    print("Testing Qdrant Deletion Functionality...")
    
    # Connect to Qdrant
    try:
        qdrant_client = QdrantClient(url="http://localhost:6333")
        print("✅ Connected to Qdrant successfully")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return
    
    # Check collection info
    try:
        collections = qdrant_client.get_collections()
        print(f"📊 Available collections: {[c.name for c in collections.collections]}")
        
        # Get collection info
        collection_info = qdrant_client.get_collection("learn_vector2")
        print(f"📊 Collection 'learn_vector2' has {collection_info.points_count} points")
        
    except Exception as e:
        print(f"❌ Failed to get collection info: {e}")
        return
    
    # Test the delete API endpoint
    print("\n🔍 Testing Delete API Endpoint...")
    
    # Test data (you can modify these to match your actual data)
    test_product_name = "MMA"
    test_product_code = "MFL55318536.pdf"
    
    try:
        response = requests.delete(
            "http://localhost:8000/delete_manual/",
            data={
                "product_name": test_product_name,
                "product_code": test_product_code
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Delete API test successful!")
            
            # Check if points were actually deleted
            try:
                updated_collection_info = qdrant_client.get_collection("learn_vector2")
                print(f"📊 Collection now has {updated_collection_info.points_count} points")
            except Exception as e:
                print(f"⚠️  Could not verify point count: {e}")
        else:
            print("❌ Delete API test failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error testing delete API: {e}")

if __name__ == "__main__":
    test_qdrant_deletion()
