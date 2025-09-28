#!/usr/bin/env python3
"""
Script to create a test user for testing user-specific inventory functionality.
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:5000"

def create_test_user():
    """Create a test user."""
    print("🔧 Creating Test User")
    print("=" * 30)
    
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    
    try:
        signup_response = requests.post(f"{BASE_URL}/api/auth/signup", json=test_user)
        
        if signup_response.status_code == 200:
            result = signup_response.json()
            print(f"✅ Test user created successfully")
            print(f"   Username: {result.get('username', 'N/A')}")
            print(f"   Email: {result.get('email', 'N/A')}")
            print(f"   User ID: {result.get('user_id', 'N/A')}")
            return True
        elif signup_response.status_code == 400:
            error_data = signup_response.json()
            if "already exists" in error_data.get('error', ''):
                print(f"ℹ️  Test user already exists")
                return True
            else:
                print(f"❌ User creation failed: {error_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ User creation failed: {signup_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

def test_login():
    """Test login with the created user."""
    print("\n🔐 Testing Login")
    print("=" * 30)
    
    login_data = {
        "username": "testuser",
        "password": "test123"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            result = login_response.json()
            print(f"✅ Login successful")
            print(f"   Username: {result.get('username', 'N/A')}")
            print(f"   User ID: {result.get('user_id', 'N/A')}")
            print(f"   Session Token: {result.get('session_token', 'N/A')[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

if __name__ == "__main__":
    if create_test_user():
        if test_login():
            print("\n🎉 Test user setup completed successfully!")
        else:
            print("\n❌ Login test failed")
    else:
        print("\n❌ Failed to create test user")
