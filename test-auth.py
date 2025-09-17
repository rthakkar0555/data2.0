#!/usr/bin/env python3
"""
Test script for the authentication system
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_signup():
    """Test user signup"""
    print("Testing user signup...")
    
    signup_data = {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "role": "user"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Signup successful!")
            print(f"   User ID: {data['user']['id']}")
            print(f"   Email: {data['user']['email']}")
            print(f"   Role: {data['user']['role']}")
            return data['access_token']
        else:
            print(f"❌ Signup failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return None

def test_login():
    """Test admin login"""
    print("\nTesting admin login...")
    
    login_data = {
        "email": "admin@manualbase.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful!")
            print(f"   User ID: {data['user']['id']}")
            print(f"   Email: {data['user']['email']}")
            print(f"   Role: {data['user']['role']}")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_get_user_info(token):
    """Test getting user info with token"""
    print("\nTesting get user info...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get user info successful!")
            print(f"   User ID: {data['id']}")
            print(f"   Email: {data['email']}")
            print(f"   Role: {data['role']}")
        else:
            print(f"❌ Get user info failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Get user info error: {e}")

def test_admin_endpoint(token):
    """Test admin-only endpoint"""
    print("\nTesting admin-only endpoint...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/admin-only", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin endpoint access successful!")
            print(f"   Message: {data['message']}")
            print(f"   User: {data['user']}")
        else:
            print(f"❌ Admin endpoint access failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Admin endpoint error: {e}")

def main():
    print("🔐 Authentication System Test")
    print("=" * 40)
    
    # Test admin login
    admin_token = test_login()
    
    if admin_token:
        # Test get user info
        test_get_user_info(admin_token)
        
        # Test admin endpoint
        test_admin_endpoint(admin_token)
    
    # Test user signup
    user_token = test_signup()
    
    if user_token:
        # Test get user info for regular user
        test_get_user_info(user_token)
        
        # Test admin endpoint with user token (should fail)
        print("\nTesting admin endpoint with user token (should fail)...")
        test_admin_endpoint(user_token)
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    main()
