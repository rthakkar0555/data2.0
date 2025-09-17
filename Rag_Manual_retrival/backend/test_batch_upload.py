#!/usr/bin/env python3
"""
Test script for batch upload functionality
"""

import requests
import json
import os
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_FILES_DIR = Path(__file__).parent.parent / "uploads"

def test_single_file_upload():
    """Test single file upload"""
    print("🧪 Testing single file upload...")
    
    # Create a test PDF file (dummy content)
    test_file_path = TEST_FILES_DIR / "test_single.pdf"
    test_file_path.parent.mkdir(exist_ok=True)
    
    # Create a simple PDF-like content for testing
    with open(test_file_path, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n")
    
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_single.pdf", f, "application/pdf")}
            data = {
                "company_name": "TestCompany",
                "product_name": "TestProduct",
                "product_code": "TEST001"
            }
            
            response = requests.post(f"{BASE_URL}/upload_pdf/", files=files, data=data)
            
            if response.status_code == 200:
                print("✅ Single file upload successful")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Single file upload failed: {response.status_code}")
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Single file upload error: {e}")
    finally:
        # Clean up test file
        if test_file_path.exists():
            test_file_path.unlink()

def test_multiple_file_upload():
    """Test multiple file upload"""
    print("\n🧪 Testing multiple file upload...")
    
    # Create test PDF files
    test_files = []
    for i in range(3):
        test_file_path = TEST_FILES_DIR / f"test_multiple_{i}.pdf"
        with open(test_file_path, "wb") as f:
            f.write(f"%PDF-1.4\n{i} 0 obj\n<<\n/Type /Catalog\n/Pages {i+1} 0 R\n>>\nendobj\n".encode())
        test_files.append(test_file_path)
    
    try:
        files = []
        for test_file in test_files:
            files.append(("files", (test_file.name, open(test_file, "rb"), "application/pdf")))
        
        data = {
            "company_name": "TestCompany",
            "product_name": "TestProduct",
            "product_code": "TEST002"
        }
        
        response = requests.post(f"{BASE_URL}/upload_multiple_pdfs/", files=files, data=data)
        
        # Close file handles
        for _, (_, file_handle, _) in files:
            file_handle.close()
        
        if response.status_code == 200:
            print("✅ Multiple file upload successful")
            result = response.json()
            print(f"Files processed: {result.get('files', [])}")
            print(f"Total chunks: {result.get('total_chunks', 0)}")
            print(f"Results: {result.get('results', [])}")
        else:
            print(f"❌ Multiple file upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Multiple file upload error: {e}")
    finally:
        # Clean up test files
        for test_file in test_files:
            if test_file.exists():
                test_file.unlink()

def test_health_check():
    """Test health check endpoint"""
    print("\n🧪 Testing health check...")
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        
        if response.status_code == 200:
            print("✅ Health check successful")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting batch upload tests...")
    
    # Test health check first
    test_health_check()
    
    # Test single file upload
    test_single_file_upload()
    
    # Test multiple file upload
    test_multiple_file_upload()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()

