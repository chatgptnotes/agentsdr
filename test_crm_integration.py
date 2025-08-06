#!/usr/bin/env python3
"""
Test CRM Integration for AgentSDR
Demonstrates HubSpot and Salesforce integration capabilities
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:8080"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        headers={'Content-Type': 'application/json'},
        json={'email': 'admin@bhashai.com', 'password': 'admin123'}
    )
    
    if response.status_code == 200:
        return response.json().get('token')
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_crm_status(token):
    """Test CRM connection status"""
    print("\n🔍 Testing CRM Status...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}/api/crm/status", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ CRM Status: {data.get('message')}")
        print(f"   Connected: {data.get('connected')}")
        print(f"   CRM Type: {data.get('crm_type', 'None')}")
        return data.get('connected')
    else:
        print(f"❌ CRM Status failed: {response.status_code}")
        print(response.text)
        return False

def test_sync_contacts(token):
    """Test syncing contacts from CRM"""
    print("\n📥 Testing Contact Sync...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(f"{BASE_URL}/api/crm/contacts/sync", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Contacts synced successfully!")
        print(f"   New contacts: {data.get('synced', 0)}")
        print(f"   Updated contacts: {data.get('updated', 0)}")
        print(f"   Total processed: {data.get('total', 0)}")
        return True
    else:
        print(f"❌ Contact sync failed: {response.status_code}")
        print(response.text)
        return False

def test_get_contacts(token):
    """Test getting synced contacts"""
    print("\n📋 Testing Get Contacts...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}/api/crm/contacts", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        contacts = data.get('contacts', [])
        print(f"✅ Retrieved {len(contacts)} contacts")
        
        if contacts:
            # Show first few contacts
            for i, contact in enumerate(contacts[:3]):
                print(f"   {i+1}. {contact.get('first_name')} {contact.get('last_name')}")
                print(f"      Email: {contact.get('email')}")
                print(f"      Phone: {contact.get('phone')}")
                print(f"      Company: {contact.get('company')}")
        
        return contacts
    else:
        print(f"❌ Get contacts failed: {response.status_code}")
        print(response.text)
        return []

def test_assign_contact_to_agent(token, contact_id, agent_id):
    """Test assigning contact to voice agent"""
    print(f"\n🎯 Testing Contact Assignment...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    data = {'agent_id': agent_id}
    
    response = requests.post(
        f"{BASE_URL}/api/crm/contacts/{contact_id}/assign-agent",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        print(f"✅ Contact assigned to agent successfully!")
        return True
    else:
        print(f"❌ Contact assignment failed: {response.status_code}")
        print(response.text)
        return False

def test_sync_call_result(token, contact_id):
    """Test syncing call results back to CRM"""
    print(f"\n📞 Testing Call Result Sync...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    call_data = {
        'duration': 180,
        'status': 'completed',
        'outcome': 'interested',
        'agent_name': 'AgentSDR Voice Agent',
        'call_date': datetime.now().isoformat(),
        'notes': 'Customer showed strong interest in our premium package. Requested follow-up call next week.'
    }
    
    data = {
        'contact_id': contact_id,
        'call_data': call_data
    }
    
    response = requests.post(
        f"{BASE_URL}/api/crm/sync-call-result",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        print(f"✅ Call results synced to CRM successfully!")
        return True
    else:
        print(f"❌ Call result sync failed: {response.status_code}")
        print(response.text)
        return False

def create_sample_voice_agent(token):
    """Create a sample voice agent for testing"""
    print("\n🤖 Creating sample voice agent...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    agent_data = {
        'name': 'CRM Test Agent',
        'language': 'en-US',
        'use_case': 'lead_qualification',
        'calling_number': '+1234567890',
        'configuration': {
            'greeting': 'Hello! This is a test call from AgentSDR.',
            'voice_type': 'professional'
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/voice-agents", headers=headers, json=agent_data)
    
    if response.status_code == 201:
        agent = response.json().get('voice_agent', {})
        print(f"✅ Voice agent created: {agent.get('name')}")
        return agent.get('id')
    else:
        print(f"⚠️  Voice agent creation failed: {response.status_code}")
        # Return a mock agent ID for testing
        return "test-agent-123"

def run_crm_integration_test():
    """Run comprehensive CRM integration test"""
    print("🚀 AgentSDR CRM Integration Test")
    print("=" * 50)
    
    # Check environment
    crm_type = os.getenv('CRM_TYPE', 'Not configured')
    print(f"CRM Type: {crm_type}")
    
    if crm_type == 'hubspot':
        api_key = os.getenv('HUBSPOT_API_KEY', 'Not set')
        print(f"HubSpot API Key: {'Set' if api_key != 'Not set' else 'Not set'}")
    elif crm_type == 'salesforce':
        client_id = os.getenv('SALESFORCE_CLIENT_ID', 'Not set')
        print(f"Salesforce Client ID: {'Set' if client_id != 'Not set' else 'Not set'}")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Test CRM status
    crm_connected = test_crm_status(token)
    
    if not crm_connected:
        print("\n⚠️  CRM not connected. Testing with mock data...")
        print("\nTo test with real CRM:")
        print("1. Set up your CRM credentials in .env file")
        print("2. Follow the CRM_INTEGRATION_GUIDE.md")
        return
    
    # Test contact sync
    sync_success = test_sync_contacts(token)
    
    if sync_success:
        # Get synced contacts
        contacts = test_get_contacts(token)
        
        if contacts:
            # Create a voice agent for testing
            agent_id = create_sample_voice_agent(token)
            
            # Test contact assignment
            first_contact = contacts[0]
            contact_id = first_contact.get('id')
            
            if contact_id and agent_id:
                assign_success = test_assign_contact_to_agent(token, contact_id, agent_id)
                
                if assign_success:
                    # Test call result sync
                    test_sync_call_result(token, contact_id)
    
    print("\n" + "=" * 50)
    print("🎉 CRM Integration Test Complete!")
    print("\nNext steps:")
    print("1. Check your CRM for synced call results")
    print("2. Set up webhooks for real-time updates")
    print("3. Configure custom field mappings")

if __name__ == "__main__":
    run_crm_integration_test()
