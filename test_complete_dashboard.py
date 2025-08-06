#!/usr/bin/env python3
"""
Comprehensive test for AgentSDR Dashboard functionality
Tests authentication, dashboard stats, voice agents, and enterprise features
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_login(email, password):
    """Test user login"""
    print(f"\n🔐 Testing login for {email}...")
    
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
        print(f"   Enterprise: {data.get('user', {}).get('enterprise_id', 'None')}")
        return data.get('token')
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def test_dashboard_stats(token):
    """Test dashboard statistics API"""
    print("\n📊 Testing dashboard stats API...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Dashboard stats retrieved successfully!")
        print(f"   Voice Agents: {data.get('voice_agents', 0)}")
        print(f"   Contacts: {data.get('contacts', 0)}")
        print(f"   Active Contacts: {data.get('active_contacts', 0)}")
        print(f"   Response Rate: {data.get('response_rate', 0)}%")
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

def test_create_voice_agent(token):
    """Test creating a voice agent"""
    print("\n🎯 Testing voice agent creation...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    agent_data = {
        'name': 'Test Agent',
        'language': 'en-US',
        'use_case': 'customer_support',
        'calling_number': '+1234567890',
        'configuration': {
            'greeting': 'Hello, how can I help you today?',
            'voice_type': 'professional'
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/voice-agents", headers=headers, json=agent_data)
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Voice agent created successfully!")
        print(f"   Agent ID: {data.get('voice_agent', {}).get('id', 'Unknown')}")
        print(f"   Name: {data.get('voice_agent', {}).get('name', 'Unknown')}")
        return data.get('voice_agent')
    else:
        print(f"❌ Voice agent creation failed: {response.status_code}")
        print(response.text)
        return None

def test_enterprises(token):
    """Test enterprises API"""
    print("\n🏢 Testing enterprises API...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}/api/enterprises", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Enterprises retrieved successfully!")
        print(f"   Found {len(data.get('enterprises', []))} enterprises")
        return data
    else:
        print(f"❌ Enterprises failed: {response.status_code}")
        print(response.text)
        return None

def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🚀 AgentSDR Dashboard Comprehensive Test")
    print("=" * 60)
    
    # Test different user types
    test_users = [
        ('admin@bhashai.com', 'admin123', 'Admin'),
        ('manager@bhashai.com', 'manager123', 'Manager'),
        ('user@bhashai.com', 'user123', 'User')
    ]
    
    results = {}
    
    for email, password, role in test_users:
        print(f"\n{'='*20} Testing {role} User {'='*20}")
        
        # Login
        token = test_login(email, password)
        if not token:
            results[role] = {'login': False}
            continue
        
        # Test dashboard stats
        stats = test_dashboard_stats(token)
        
        # Test voice agents
        voice_agents = test_voice_agents(token)
        
        # Test enterprises (may fail for regular users)
        enterprises = test_enterprises(token)
        
        # Test voice agent creation (only for admin/manager)
        created_agent = None
        if role in ['Admin', 'Manager']:
            created_agent = test_create_voice_agent(token)
        
        results[role] = {
            'login': True,
            'dashboard_stats': stats is not None,
            'voice_agents': voice_agents is not None,
            'enterprises': enterprises is not None,
            'create_agent': created_agent is not None
        }
    
    # Print summary
    print(f"\n{'='*60}")
    print("📋 Test Summary:")
    print("=" * 60)
    
    for role, tests in results.items():
        print(f"\n{role} User:")
        for test_name, passed in tests.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    # Overall status
    all_critical_passed = all(
        results.get(role, {}).get('login', False) and 
        results.get(role, {}).get('dashboard_stats', False) and
        results.get(role, {}).get('voice_agents', False)
        for role in ['Admin', 'Manager', 'User']
    )
    
    print(f"\n{'='*60}")
    if all_critical_passed:
        print("🎉 ALL CRITICAL TESTS PASSED! Dashboard is fully functional!")
    else:
        print("⚠️  Some critical tests failed. Check the results above.")
    print("=" * 60)

if __name__ == "__main__":
    run_comprehensive_test()
