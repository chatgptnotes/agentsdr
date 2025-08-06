#!/usr/bin/env python3
"""
Test the dashboard API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_login():
    """Test login and get auth token"""
    print("🔐 Testing login...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        headers={'Content-Type': 'application/json'},
        json={'email': 'admin@bhashai.com', 'password': 'admin123'}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"   User: {data.get('user', {}).get('name', 'Unknown')}")
        print(f"   Role: {data.get('user', {}).get('role', 'Unknown')}")
        return data.get('token')
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_dashboard_stats(token):
    """Test dashboard stats API"""
    print("\n📊 Testing dashboard stats API...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Dashboard stats retrieved successfully!")
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"❌ Dashboard stats failed: {response.status_code}")
        print(response.text)
        return None

def test_voice_agents(token):
    """Test voice agents API"""
    print("\n🤖 Testing voice agents API...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}/api/voice-agents", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Voice agents retrieved successfully!")
        print(f"   Found {len(data.get('voice_agents', []))} voice agents")
        return data
    else:
        print(f"❌ Voice agents failed: {response.status_code}")
        print(response.text)
        return None

def main():
    print("🚀 Testing AgentSDR Dashboard API")
    print("=" * 50)
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Test dashboard stats
    stats = test_dashboard_stats(token)
    
    # Test voice agents
    agents = test_voice_agents(token)
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   ✅ Login: {'Success' if token else 'Failed'}")
    print(f"   ✅ Dashboard Stats: {'Success' if stats else 'Failed'}")
    print(f"   ✅ Voice Agents: {'Success' if agents else 'Failed'}")

if __name__ == "__main__":
    main()
