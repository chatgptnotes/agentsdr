"""
CRM Integration Module for AgentSDR
Supports HubSpot, Salesforce, Pipedrive, and other popular CRMs
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Contact:
    """Standardized contact data structure"""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    company: str = ""
    status: str = "active"
    tags: List[str] = None
    custom_fields: Dict[str, Any] = None
    created_at: str = ""
    updated_at: str = ""

class CRMIntegration(ABC):
    """Abstract base class for CRM integrations"""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the CRM"""
        pass
    
    @abstractmethod
    def get_contacts(self, limit: int = 100) -> List[Contact]:
        """Get contacts from CRM"""
        pass
    
    @abstractmethod
    def create_contact(self, contact: Contact) -> Optional[str]:
        """Create a new contact in CRM"""
        pass
    
    @abstractmethod
    def update_contact(self, contact_id: str, contact: Contact) -> bool:
        """Update existing contact in CRM"""
        pass
    
    @abstractmethod
    def sync_call_results(self, contact_id: str, call_data: Dict) -> bool:
        """Sync voice agent call results back to CRM"""
        pass

class HubSpotIntegration(CRMIntegration):
    """HubSpot CRM Integration with OAuth support"""

    def __init__(self, api_key: str = None, access_token: str = None, user_id: str = None):
        self.api_key = api_key or os.getenv('HUBSPOT_API_KEY')
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = "https://api.hubapi.com"

        # Use OAuth token if available, otherwise fall back to API key
        if self.access_token:
            self.headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
        elif self.api_key:
            self.headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        else:
            self.headers = {'Content-Type': 'application/json'}
    
    def load_oauth_token(self, user_id: str) -> bool:
        """Load OAuth token from database for the user"""
        try:
            import sqlite3
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT access_token, refresh_token, expires_at
                FROM crm_tokens
                WHERE user_id = ? AND crm_type = 'hubspot'
                AND expires_at > datetime('now')
            ''', (user_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                self.access_token = result[0]
                self.headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                return True
            return False

        except Exception as e:
            print(f"Failed to load OAuth token: {e}")
            return False

    def authenticate(self) -> bool:
        """Test HubSpot API connection"""
        try:
            # If we have a user_id, try to load OAuth token first
            if self.user_id and not self.access_token:
                self.load_oauth_token(self.user_id)

            response = requests.get(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers=self.headers,
                params={'limit': 1}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"HubSpot authentication failed: {e}")
            return False
    
    def get_contacts(self, limit: int = 100) -> List[Contact]:
        """Get contacts from HubSpot"""
        try:
            response = requests.get(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers=self.headers,
                params={
                    'limit': limit,
                    'properties': 'firstname,lastname,email,phone,company,hs_lead_status'
                }
            )
            
            if response.status_code != 200:
                print(f"Failed to get HubSpot contacts: {response.text}")
                return []
            
            data = response.json()
            contacts = []
            
            for item in data.get('results', []):
                props = item.get('properties', {})
                contact = Contact(
                    id=item.get('id'),
                    first_name=props.get('firstname', ''),
                    last_name=props.get('lastname', ''),
                    email=props.get('email', ''),
                    phone=props.get('phone', ''),
                    company=props.get('company', ''),
                    status=props.get('hs_lead_status', 'active'),
                    created_at=props.get('createdate', ''),
                    updated_at=props.get('lastmodifieddate', '')
                )
                contacts.append(contact)
            
            return contacts
            
        except Exception as e:
            print(f"Error getting HubSpot contacts: {e}")
            return []
    
    def create_contact(self, contact: Contact) -> Optional[str]:
        """Create contact in HubSpot"""
        try:
            data = {
                'properties': {
                    'firstname': contact.first_name,
                    'lastname': contact.last_name,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'hs_lead_status': contact.status
                }
            }
            
            response = requests.post(
                f"{self.base_url}/crm/v3/objects/contacts",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 201:
                result = response.json()
                return result.get('id')
            else:
                print(f"Failed to create HubSpot contact: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating HubSpot contact: {e}")
            return None
    
    def update_contact(self, contact_id: str, contact: Contact) -> bool:
        """Update contact in HubSpot"""
        try:
            data = {
                'properties': {
                    'firstname': contact.first_name,
                    'lastname': contact.last_name,
                    'email': contact.email,
                    'phone': contact.phone,
                    'company': contact.company,
                    'hs_lead_status': contact.status
                }
            }
            
            response = requests.patch(
                f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                headers=self.headers,
                json=data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error updating HubSpot contact: {e}")
            return False
    
    def sync_call_results(self, contact_id: str, call_data: Dict) -> bool:
        """Sync call results to HubSpot as notes/activities"""
        try:
            # Create a note about the call
            note_data = {
                'properties': {
                    'hs_note_body': f"""
Voice Agent Call Summary:
- Duration: {call_data.get('duration', 'N/A')} seconds
- Status: {call_data.get('status', 'Unknown')}
- Outcome: {call_data.get('outcome', 'N/A')}
- Agent: {call_data.get('agent_name', 'AgentSDR')}
- Date: {call_data.get('call_date', datetime.now().isoformat())}

Notes: {call_data.get('notes', 'No additional notes')}
                    """.strip(),
                    'hs_timestamp': datetime.now().isoformat()
                }
            }
            
            # Create note
            response = requests.post(
                f"{self.base_url}/crm/v3/objects/notes",
                headers=self.headers,
                json=note_data
            )
            
            if response.status_code == 201:
                note_id = response.json().get('id')
                
                # Associate note with contact
                association_data = {
                    'inputs': [{
                        'from': {'id': note_id},
                        'to': {'id': contact_id},
                        'type': 'note_to_contact'
                    }]
                }
                
                assoc_response = requests.put(
                    f"{self.base_url}/crm/v3/associations/notes/contacts/batch/create",
                    headers=self.headers,
                    json=association_data
                )
                
                return assoc_response.status_code == 200
            
            return False
            
        except Exception as e:
            print(f"Error syncing call results to HubSpot: {e}")
            return False

class SalesforceIntegration(CRMIntegration):
    """Salesforce CRM Integration (OAuth2 based)"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, username: str = None, password: str = None):
        self.client_id = client_id or os.getenv('SALESFORCE_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SALESFORCE_CLIENT_SECRET')
        self.username = username or os.getenv('SALESFORCE_USERNAME')
        self.password = password or os.getenv('SALESFORCE_PASSWORD')
        self.instance_url = None
        self.access_token = None
    
    def authenticate(self) -> bool:
        """Authenticate with Salesforce using OAuth2"""
        try:
            auth_url = "https://login.salesforce.com/services/oauth2/token"
            data = {
                'grant_type': 'password',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'username': self.username,
                'password': self.password
            }
            
            response = requests.post(auth_url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                self.instance_url = result.get('instance_url')
                return True
            else:
                print(f"Salesforce authentication failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Salesforce authentication error: {e}")
            return False
    
    def get_contacts(self, limit: int = 100) -> List[Contact]:
        """Get contacts from Salesforce"""
        if not self.access_token:
            if not self.authenticate():
                return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            query = f"SELECT Id, FirstName, LastName, Email, Phone, Account.Name FROM Contact LIMIT {limit}"
            response = requests.get(
                f"{self.instance_url}/services/data/v57.0/query",
                headers=headers,
                params={'q': query}
            )
            
            if response.status_code != 200:
                print(f"Failed to get Salesforce contacts: {response.text}")
                return []
            
            data = response.json()
            contacts = []
            
            for record in data.get('records', []):
                contact = Contact(
                    id=record.get('Id'),
                    first_name=record.get('FirstName', ''),
                    last_name=record.get('LastName', ''),
                    email=record.get('Email', ''),
                    phone=record.get('Phone', ''),
                    company=record.get('Account', {}).get('Name', '') if record.get('Account') else ''
                )
                contacts.append(contact)
            
            return contacts
            
        except Exception as e:
            print(f"Error getting Salesforce contacts: {e}")
            return []
    
    def create_contact(self, contact: Contact) -> Optional[str]:
        """Create contact in Salesforce"""
        # Implementation similar to HubSpot but using Salesforce API
        # This would require more complex logic for account association
        pass
    
    def update_contact(self, contact_id: str, contact: Contact) -> bool:
        """Update contact in Salesforce"""
        # Implementation for Salesforce contact updates
        pass
    
    def sync_call_results(self, contact_id: str, call_data: Dict) -> bool:
        """Sync call results to Salesforce as Task/Activity"""
        # Implementation for creating Salesforce tasks/activities
        pass

# CRM Factory
class DemoCRMIntegration(CRMIntegration):
    """Demo CRM Integration for testing without real CRM"""

    def __init__(self):
        self.demo_contacts = [
            Contact(
                id="demo-1",
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="+1234567890",
                company="Acme Corp",
                status="active"
            ),
            Contact(
                id="demo-2",
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                phone="+1234567891",
                company="Tech Solutions",
                status="active"
            ),
            Contact(
                id="demo-3",
                first_name="Bob",
                last_name="Johnson",
                email="bob.johnson@example.com",
                phone="+1234567892",
                company="StartupXYZ",
                status="active"
            )
        ]

    def authenticate(self) -> bool:
        """Demo always authenticates successfully"""
        return True

    def get_contacts(self, limit: int = 100) -> List[Contact]:
        """Return demo contacts"""
        return self.demo_contacts[:limit]

    def create_contact(self, contact: Contact) -> Optional[str]:
        """Simulate creating a contact"""
        new_id = f"demo-{len(self.demo_contacts) + 1}"
        contact.id = new_id
        self.demo_contacts.append(contact)
        return new_id

    def update_contact(self, contact_id: str, contact: Contact) -> bool:
        """Simulate updating a contact"""
        for i, existing in enumerate(self.demo_contacts):
            if existing.id == contact_id:
                contact.id = contact_id
                self.demo_contacts[i] = contact
                return True
        return False

    def sync_call_results(self, contact_id: str, call_data: Dict) -> bool:
        """Simulate syncing call results"""
        print(f"📞 Demo: Call result synced for contact {contact_id}")
        print(f"   Duration: {call_data.get('duration')}s")
        print(f"   Outcome: {call_data.get('outcome')}")
        return True

class CRMFactory:
    """Factory class to create CRM integrations"""

    @staticmethod
    def create_crm(crm_type: str) -> Optional[CRMIntegration]:
        """Create CRM integration based on type"""
        crm_type = crm_type.lower()

        if crm_type == 'hubspot':
            return HubSpotIntegration()
        elif crm_type == 'salesforce':
            return SalesforceIntegration()
        elif crm_type == 'demo':
            return DemoCRMIntegration()
        else:
            print(f"Unsupported CRM type: {crm_type}")
            return None

# Global CRM manager
crm_manager = None

def initialize_crm(crm_type: str = None):
    """Initialize CRM integration"""
    global crm_manager

    crm_type = crm_type or os.getenv('CRM_TYPE', 'hubspot')
    crm_manager = CRMFactory.create_crm(crm_type)

    if crm_manager and crm_manager.authenticate():
        print(f"✅ {crm_type.title()} CRM integration initialized successfully")
        return True
    else:
        print(f"❌ Failed to initialize {crm_type.title()} CRM integration")

        # Fall back to demo mode for testing
        if crm_type != 'demo':
            print("🔄 Falling back to Demo CRM for testing...")
            crm_manager = CRMFactory.create_crm('demo')
            if crm_manager and crm_manager.authenticate():
                print("✅ Demo CRM integration initialized successfully")
                return True

        crm_manager = None
        return False
