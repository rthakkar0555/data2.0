#!/usr/bin/env python3
"""
Simple test script for authentication endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_backend_connection():
    """Test if backend is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"✅ Backend is running (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n🔐 Testing Authentication Endpoints")
    print("=" * 40)
    
    # Test admin login
    print("Testing admin login...")
    login_data = {
        "email": "admin@manualbase.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin login successful!")
            print(f"   Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
            return data.get('access_token')
        else:
            print(f"❌ Admin login failed")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    return None

def test_user_signup():
    """Test user signup"""
    print("\nTesting user signup...")
    signup_data = {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User signup successful!")
            print(f"   Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
        else:
            print(f"❌ User signup failed")
            
    except Exception as e:
        print(f"❌ Signup error: {e}")

def main():
    print("🚀 Authentication System Test")
    print("=" * 40)
    
    # Test backend connection
    if not test_backend_connection():
        return
    
    # Test authentication endpoints
    token = test_auth_endpoints()
    
    # Test user signup
    test_user_signup()
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    main()
