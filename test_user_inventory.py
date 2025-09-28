#!/usr/bin/env python3
"""
Test script to verify user-specific inventory functionality.
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:5000"

def test_user_inventory():
    """Test user-specific inventory functionality."""
    print("🧪 Testing User-Specific Inventory Functionality")
    print("=" * 50)
    
    # Test user credentials
    test_user = {
        "username": "testuser",
        "password": "test123"
    }
    
    # Step 1: Login to get session token
    print("\n1. Testing user login...")
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=test_user)
        if login_response.status_code == 200:
            login_data = login_response.json()
            session_token = login_data["session_token"]
            user_id = login_data["user_id"]
            username = login_data["username"]
            print(f"✅ Login successful for user: {username}")
            print(f"   User ID: {user_id}")
            print(f"   Session Token: {session_token[:20]}...")
        else:
            print(f"❌ Login failed: {login_response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Test user-specific inventory endpoint
    print("\n2. Testing user-specific inventory endpoint...")
    try:
        headers = {
            "Authorization": f"Bearer {session_token}"
        }
        
        inventory_response = requests.get(f"{BASE_URL}/api/inventory/inventory", headers=headers)
        if inventory_response.status_code == 200:
            inventory_data = inventory_response.json()
            print(f"✅ Inventory endpoint accessible")
            print(f"   Success: {inventory_data.get('success', False)}")
            print(f"   Products count: {len(inventory_data.get('products', []))}")
            
            # Display products if any
            products = inventory_data.get('products', [])
            if products:
                print("   Products:")
                for product in products:
                    print(f"     - {product['name']}: {product['quantity']}")
            else:
                print("   No products found for this user")
        else:
            print(f"❌ Inventory endpoint failed: {inventory_response.text}")
            return False
    except Exception as e:
        print(f"❌ Inventory endpoint error: {e}")
        return False
    
    # Step 3: Test user-specific stats endpoint
    print("\n3. Testing user-specific stats endpoint...")
    try:
        stats_response = requests.get(f"{BASE_URL}/api/inventory/stats", headers=headers)
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"✅ Stats endpoint accessible")
            print(f"   Success: {stats_data.get('success', False)}")
            
            if 'stats' in stats_data:
                stats = stats_data['stats']
                print(f"   Total Products: {stats.get('total_products', 0)}")
                print(f"   Total Quantity: {stats.get('total_quantity', 0)}")
                print(f"   Low Stock Count: {stats.get('low_stock_count', 0)}")
        else:
            print(f"❌ Stats endpoint failed: {stats_response.text}")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")
        return False
    
    # Step 4: Test adding a product for this user
    print("\n4. Testing adding a product for the user...")
    try:
        add_product_data = {
            "text": "Add 5 packets of milk"
        }
        
        add_response = requests.post(
            f"{BASE_URL}/api/inventory/command", 
            json=add_product_data, 
            headers=headers
        )
        
        if add_response.status_code == 200:
            add_result = add_response.json()
            print(f"✅ Product addition successful")
            print(f"   Success: {add_result.get('success', False)}")
            print(f"   Action: {add_result.get('action', 'N/A')}")
            print(f"   Product: {add_result.get('product', 'N/A')}")
            print(f"   Quantity: {add_result.get('quantity', 'N/A')}")
        else:
            print(f"❌ Product addition failed: {add_response.text}")
            return False
    except Exception as e:
        print(f"❌ Product addition error: {e}")
        return False
    
    # Step 5: Verify the product was added for this user
    print("\n5. Verifying product was added for the user...")
    try:
        inventory_response = requests.get(f"{BASE_URL}/api/inventory/inventory", headers=headers)
        if inventory_response.status_code == 200:
            inventory_data = inventory_response.json()
            products = inventory_data.get('products', [])
            
            # Check if our test product exists
            milk_products = [p for p in products if 'milk' in p.get('name', '').lower()]
            if milk_products:
                print(f"✅ Product 'milk' found in user's inventory")
                for product in milk_products:
                    print(f"   - {product['name']}: {product['quantity']}")
            else:
                print(f"❌ Product 'milk' not found in user's inventory")
                return False
        else:
            print(f"❌ Inventory verification failed: {inventory_response.text}")
            return False
    except Exception as e:
        print(f"❌ Inventory verification error: {e}")
        return False
    
    print("\n🎉 All tests passed! User-specific inventory functionality is working correctly.")
    return True

if __name__ == "__main__":
    test_user_inventory()
