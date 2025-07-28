#!/usr/bin/env python3
"""
Test the new superadmin user murali@drmhope.com
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

SUPABASE_HEADERS = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json'
}

def test_new_admin():
    """Test the new superadmin user"""
    
    print("=" * 60)
    print(" Testing New Superadmin: murali@drmhope.com")
    print("=" * 60)
    
    # Test new admin user
    print("\n🔍 Testing murali@drmhope.com...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?email=eq.murali@drmhope.com",
            headers=SUPABASE_HEADERS
        )
        
        if response.status_code == 200:
            users = response.json()
            if users and len(users) > 0:
                user = users[0]
                print(f"✅ User found: {user['name']}")
                print(f"   Email: {user['email']}")
                print(f"   Role: {user['role']}")
                print(f"   Status: {user['status']}")
                print(f"   Organization: {user['organization']}")
                print(f"   Enterprise ID: {user.get('enterprise_id', 'None')}")
                
                if user['role'] == 'admin' and user['status'] == 'active':
                    print("✅ New superadmin is properly configured!")
                    return True
                else:
                    print("❌ User exists but not properly configured as admin")
                    return False
            else:
                print("❌ User not found")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing new admin: {e}")
        return False

    # Test old admin user status
    print("\n🔍 Testing old admin status (admin@drmhope.com)...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?email=eq.admin@drmhope.com",
            headers=SUPABASE_HEADERS
        )
        
        if response.status_code == 200:
            users = response.json()
            if users and len(users) > 0:
                user = users[0]
                print(f"📋 Old admin status: {user['email']}")
                print(f"   Role: {user['role']}")
                print(f"   Status: {user['status']}")
                
                if user['role'] != 'admin':
                    print("✅ Old admin properly downgraded")
                else:
                    print("⚠️  Old admin still has admin role")
            else:
                print("✅ Old admin user removed")
        else:
            print(f"❌ API error checking old admin: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking old admin: {e}")

if __name__ == "__main__":
    success = test_new_admin()
    
    if success:
        print("\n🎉 SUCCESS! New superadmin is ready:")
        print("📧 Email: murali@drmhope.com")
        print("👤 Role: admin")
        print("🔑 You can now sign up with this email in Clerk")
    else:
        print("\n❌ Test failed - please check the configuration")
        exit(1)