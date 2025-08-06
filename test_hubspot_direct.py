#!/usr/bin/env python3
"""
Direct HubSpot API Test
Test the HubSpot API key directly to verify it works
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_hubspot_api():
    """Test HubSpot API directly"""
    api_key = os.getenv('HUBSPOT_API_KEY')
    print(f"🔍 Testing HubSpot API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
    
    if not api_key:
        print("❌ No HubSpot API key found in environment")
        return False
    
    # Test API connection
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("🔍 Testing HubSpot API connection...")
        response = requests.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers,
            params={'limit': 1}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ HubSpot API connection successful!")
            print(f"📋 Total contacts available: {data.get('total', 'Unknown')}")
            
            # Show first contact if available
            results = data.get('results', [])
            if results:
                contact = results[0]
                props = contact.get('properties', {})
                print(f"👤 Sample contact: {props.get('firstname', '')} {props.get('lastname', '')}")
                print(f"📧 Email: {props.get('email', 'N/A')}")
            
            return True
        else:
            print(f"❌ HubSpot API connection failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing HubSpot API: {e}")
        return False

def test_environment():
    """Test environment variable loading"""
    print("🔍 Testing Environment Variables:")
    print(f"   CRM_TYPE: {os.getenv('CRM_TYPE', 'Not set')}")
    print(f"   HUBSPOT_API_KEY: {'Set' if os.getenv('HUBSPOT_API_KEY') else 'Not set'}")
    print(f"   JWT_SECRET_KEY: {'Set' if os.getenv('JWT_SECRET_KEY') else 'Not set'}")

if __name__ == "__main__":
    print("🚀 Direct HubSpot API Test")
    print("=" * 40)
    
    test_environment()
    print()
    
    success = test_hubspot_api()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 HubSpot integration is ready!")
        print("You can now use the CRM features in AgentSDR")
    else:
        print("⚠️  HubSpot integration needs attention")
        print("Check your API key and permissions")
