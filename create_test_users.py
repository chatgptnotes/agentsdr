#!/usr/bin/env python3
"""
Create test users in Supabase for dashboard testing
"""

import os
import sys
import requests
import json
import bcrypt
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

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
        
        print(f"{method} {endpoint}: {response.status_code}")
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Request error: {e}")
        return None

def create_test_users():
    """Create test users in Supabase"""
    print("🚀 Creating test users in Supabase...")
    
    # First, create a test enterprise
    enterprise_data = {
        'name': 'Test Enterprise',
        'description': 'Test enterprise for dashboard testing',
        'status': 'active'
    }
    
    print("📊 Creating test enterprise...")
    enterprise = supabase_request('POST', 'enterprises', enterprise_data)
    if not enterprise:
        print("❌ Failed to create enterprise")
        return
    
    enterprise_id = enterprise[0]['id'] if isinstance(enterprise, list) else enterprise['id']
    print(f"✅ Created enterprise: {enterprise_id}")
    
    # Create test users
    test_users = [
        {
            'email': 'superadmin@agentsdr.com',
            'name': 'Super Admin',
            'role': 'super_admin',
            'status': 'active',
            'enterprise_id': enterprise_id,
            'password_hash': hash_password('superadmin123')
        },
        {
            'email': 'admin@agentsdr.com',
            'name': 'Admin User',
            'role': 'admin',
            'status': 'active',
            'enterprise_id': enterprise_id,
            'password_hash': hash_password('admin123')
        },
        {
            'email': 'user@agentsdr.com',
            'name': 'Regular User',
            'role': 'user',
            'status': 'active',
            'enterprise_id': enterprise_id,
            'password_hash': hash_password('user123')
        }
    ]
    
    print("👥 Creating test users...")
    for user_data in test_users:
        user = supabase_request('POST', 'users', user_data)
        if user:
            print(f"✅ Created user: {user_data['email']} ({user_data['role']})")
        else:
            print(f"❌ Failed to create user: {user_data['email']}")
    
    # Create some sample voice agents
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
                'welcome_message': 'Hello! I\'m your sales assistant. How can I help you today?'
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
                'welcome_message': 'Hi! I\'m calling about our amazing products.'
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
                'welcome_message': 'Hi! How can I help you via WhatsApp?'
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
    
    # Create sample contacts
    print("👥 Creating sample contacts...")
    for i, agent_id in enumerate(created_agents):
        for j in range(10):  # 10 contacts per agent
            contact_data = {
                'name': f'Contact {i+1}-{j+1}',
                'phone': f'+1555{i:03d}{j:04d}',
                'voice_agent_id': agent_id,
                'enterprise_id': enterprise_id,
                'status': 'active' if j < 8 else 'inactive'
            }
            
            contact = supabase_request('POST', 'contacts', contact_data)
            if contact:
                print(f"✅ Created contact: {contact_data['name']}")
    
    print("\n🎉 Test data creation completed!")
    print(f"🔗 Test the dashboard at: http://localhost:8000/dashboard.html")
    print(f"🔑 Login credentials:")
    print(f"   Super Admin: superadmin@agentsdr.com / superadmin123")
    print(f"   Admin: admin@agentsdr.com / admin123")
    print(f"   User: user@agentsdr.com / user123")

if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase configuration. Check your .env file.")
        sys.exit(1)
    
    create_test_users()
