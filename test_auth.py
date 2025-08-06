#!/usr/bin/env python3
"""
Test script for AgentSDR Authentication System
Tests the unified login flow and role-based redirects
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your server runs on different port

def test_login(email, password, expected_role=None):
    """Test login functionality"""
    print(f"\n🔐 Testing login for: {email}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            headers={'Content-Type': 'application/json'},
            json={'email': email, 'password': password}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful!")
            print(f"   User: {data.get('user', {}).get('name', 'Unknown')}")
            print(f"   Role: {data.get('user', {}).get('role', 'Unknown')}")
            print(f"   Redirect: {data.get('redirect_url', 'No redirect specified')}")
            
            if expected_role and data.get('user', {}).get('role') == expected_role:
                print(f"✅ Role matches expected: {expected_role}")
            elif expected_role:
                print(f"❌ Role mismatch. Expected: {expected_role}, Got: {data.get('user', {}).get('role')}")
            
            return True, data
        else:
            error_data = response.json()
            print(f"❌ Login failed: {error_data.get('error', 'Unknown error')}")
            return False, error_data
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed. Is the server running on {BASE_URL}?")
        return False, None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

def test_dashboard_access(redirect_url, cookies=None):
    """Test if dashboard is accessible"""
    print(f"\n🌐 Testing dashboard access: {redirect_url}")
    
    try:
        response = requests.get(f"{BASE_URL}{redirect_url}", cookies=cookies)
        
        if response.status_code == 200:
            print(f"✅ Dashboard accessible")
            return True
        else:
            print(f"❌ Dashboard not accessible (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing dashboard: {str(e)}")
        return False

def main():
    """Run authentication tests"""
    print("🚀 AgentSDR Authentication System Test")
    print("=" * 50)
    
    # Test cases: (email, password, expected_role)
    test_cases = [
        ("superadmin@agentsdr.com", "superadmin123", "super_admin"),
        ("admin@agentsdr.com", "admin123", "admin"),
        ("user@agentsdr.com", "user123", "user"),
        ("nonexistent@agentsdr.com", "wrongpass", None),  # Should fail
    ]
    
    results = []
    
    for email, password, expected_role in test_cases:
        success, data = test_login(email, password, expected_role)
        results.append((email, success, data))
        
        if success and data and 'redirect_url' in data:
            # Test dashboard access
            test_dashboard_access(data['redirect_url'])
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    successful_logins = sum(1 for _, success, _ in results if success)
    total_tests = len([tc for tc in test_cases if tc[2] is not None])  # Exclude expected failures
    
    print(f"   Successful logins: {successful_logins}/{total_tests}")
    
    for email, success, data in results:
        status = "✅" if success else "❌"
        role = data.get('user', {}).get('role', 'N/A') if data else 'N/A'
        print(f"   {status} {email} ({role})")
    
    if successful_logins == total_tests:
        print("\n🎉 All authentication tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - successful_logins} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
