#!/usr/bin/env python3
"""
Populate sample data for testing the dashboard real data integration
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def supabase_request(method, endpoint, data=None):
    """Make request to Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Request error: {e}")
        return None

def create_sample_data():
    """Create sample data for testing"""
    print("🚀 Creating sample data for AgentSDR dashboard...")

    # 1. Create sample enterprise (using existing schema)
    enterprise_data = {
        'name': 'Sample Enterprise Inc',
        'description': 'A sample enterprise for testing',
        'status': 'active'
    }

    print("📊 Creating sample enterprise...")
    enterprise = supabase_request('POST', 'enterprises', enterprise_data)
    if not enterprise:
        print("❌ Failed to create enterprise")
        return

    enterprise_id = enterprise[0]['id'] if isinstance(enterprise, list) else enterprise['id']
    print(f"✅ Created enterprise: {enterprise_id}")

    # 2. Create sample voice agents (using existing schema)
    voice_agents_data = [
        {
            'title': 'Sales Assistant AI',
            'description': 'AI assistant for handling sales inquiries',
            'url': 'https://api.agentsdr.com/voice/sales',
            'category': 'Inbound Calls',
            'status': 'active',
            'enterprise_id': enterprise_id,
            'configuration': {
                'language': 'en',
                'use_case': 'sales',
                'welcome_message': 'Hello! I\'m your sales assistant. How can I help you today?',
                'agent_prompt': 'You are a helpful sales assistant.'
            }
        },
        {
            'title': 'Outbound Sales AI',
            'description': 'AI assistant for making outbound sales calls',
            'url': 'https://api.agentsdr.com/voice/outbound',
            'category': 'Outbound Calls',
            'status': 'active',
            'enterprise_id': enterprise_id,
            'configuration': {
                'language': 'en',
                'use_case': 'sales',
                'welcome_message': 'Hi! I\'m calling about our amazing products.',
                'agent_prompt': 'You are a proactive outbound sales agent.'
            }
        },
        {
            'title': 'Support Helper AI',
            'description': 'AI assistant for customer support',
            'url': 'https://api.agentsdr.com/voice/support',
            'category': 'Inbound Calls',
            'status': 'active',
            'enterprise_id': enterprise_id,
            'configuration': {
                'language': 'en',
                'use_case': 'support',
                'welcome_message': 'Hello! I\'m here to help with your support needs.',
                'agent_prompt': 'You are a helpful customer support agent.'
            }
        },
        {
            'title': 'WhatsApp Assistant',
            'description': 'AI assistant for WhatsApp messaging',
            'url': 'https://api.agentsdr.com/whatsapp/assistant',
            'category': 'WhatsApp Messages',
            'status': 'active',
            'enterprise_id': enterprise_id,
            'configuration': {
                'language': 'en',
                'use_case': 'support',
                'welcome_message': 'Hi! How can I help you via WhatsApp?',
                'agent_prompt': 'You are a friendly WhatsApp assistant.'
            }
        }
    ]

    print("🤖 Creating sample voice agents...")
    created_agents = []
    for agent_data in voice_agents_data:
        agent = supabase_request('POST', 'voice_agents', agent_data)
        if agent:
            agent_id = agent[0]['id'] if isinstance(agent, list) else agent['id']
            created_agents.append(agent_id)
            print(f"✅ Created voice agent: {agent_data['title']}")

    # 3. Create sample contacts
    contacts_data = []
    for i, agent_id in enumerate(created_agents):
        for j in range(5):  # 5 contacts per agent
            contact_data = {
                'name': f'Contact {i+1}-{j+1}',
                'phone': f'+1555{i:03d}{j:04d}',
                'voice_agent_id': agent_id,
                'enterprise_id': enterprise_id,
                'status': 'active' if j < 4 else 'inactive'
            }
            contacts_data.append(contact_data)

    print("👥 Creating sample contacts...")
    for contact_data in contacts_data:
        contact = supabase_request('POST', 'contacts', contact_data)
        if contact:
            print(f"✅ Created contact: {contact_data['name']}")

    print("\n🎉 Sample data creation completed!")
    print(f"📊 Created:")
    print(f"   - 1 Enterprise")
    print(f"   - {len(voice_agents_data)} Voice Agents")
    print(f"   - {len(contacts_data)} Contacts")
    print(f"\n🔗 Test the dashboard at: http://localhost:8000/dashboard.html")
    print(f"🔑 Login with: user@agentsdr.com / user123")

if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase configuration. Check your .env file.")
        sys.exit(1)
    
    create_sample_data()
