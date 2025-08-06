#!/usr/bin/env python3
"""
Debug login issues for AgentSDR
"""

import sqlite3
import bcrypt
import requests
import json

def check_database():
    """Check if users exist in database"""
    print("🔍 Checking SQLite database...")
    
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table doesn't exist!")
            return False
        
        # Get all users
        cursor.execute('SELECT email, name, role, status, password_hash FROM users')
        users = cursor.fetchall()
        
        print(f"📋 Found {len(users)} users in database:")
        for user in users:
            email, name, role, status, password_hash = user
            print(f"  📧 {email} | {name} | {role} | {status}")
            print(f"     Password hash: {password_hash[:50]}...")
        
        conn.close()
        return len(users) > 0
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_password_hash():
    """Test password hashing"""
    print("\n🔐 Testing password hashing...")
    
    test_password = "admin123"
    
    # Hash the password
    hashed = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"Generated hash: {hashed}")
    
    # Verify the password
    is_valid = bcrypt.checkpw(test_password.encode('utf-8'), hashed.encode('utf-8'))
    print(f"Password verification: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    return is_valid

def test_login_api():
    """Test login API endpoint"""
    print("\n🌐 Testing login API...")
    
    test_credentials = [
        ("admin@bhashai.com", "admin123"),
        ("manager@bhashai.com", "manager123"),
        ("user@bhashai.com", "user123")
    ]
    
    for email, password in test_credentials:
        print(f"\n🔑 Testing login: {email}")
        
        try:
            response = requests.post(
                "http://localhost:8080/api/auth/login",
                headers={'Content-Type': 'application/json'},
                json={'email': email, 'password': password},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful!")
                print(f"   User: {data.get('user', {}).get('name', 'Unknown')}")
                print(f"   Role: {data.get('user', {}).get('role', 'Unknown')}")
                return True
            else:
                print(f"❌ Login failed")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"   Raw response: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Is the server running on port 8080?")
        except Exception as e:
            print(f"❌ Request error: {e}")
    
    return False

def main():
    """Run all debug tests"""
    print("🚀 AgentSDR Login Debug Tool")
    print("=" * 50)
    
    # Check database
    db_ok = check_database()
    
    # Test password hashing
    hash_ok = test_password_hash()
    
    # Test login API
    api_ok = test_login_api()
    
    print("\n" + "=" * 50)
    print("📊 Debug Summary:")
    print(f"   Database: {'✅ OK' if db_ok else '❌ Issues'}")
    print(f"   Password Hashing: {'✅ OK' if hash_ok else '❌ Issues'}")
    print(f"   Login API: {'✅ OK' if api_ok else '❌ Issues'}")
    
    if not db_ok:
        print("\n💡 Suggestion: Run the server once to initialize the database")
    if not api_ok:
        print("\n💡 Suggestion: Check server logs for authentication errors")

if __name__ == "__main__":
    main()
