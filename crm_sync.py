"""
AgentSDR CRM Synchronization System
Real-time data synchronization with major CRM platforms
Supports Salesforce, HubSpot, Zoho, Pipedrive, and custom integrations
"""

import os
import json
import requests
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import hashlib
from dotenv import load_dotenv

load_dotenv()

class CRMType(Enum):
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    ZOHO = "zoho"
    PIPEDRIVE = "pipedrive"
    CUSTOM = "custom"

class SyncDirection(Enum):
    BIDIRECTIONAL = "bidirectional"
    TO_CRM = "to_crm"
    FROM_CRM = "from_crm"

class SyncStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"

@dataclass
class CRMMapping:
    agentsdr_field: str
    crm_field: str
    field_type: str
    transformation: Optional[str] = None
    is_required: bool = False

@dataclass
class SyncResult:
    success: bool
    records_processed: int
    records_success: int
    records_failed: int
    errors: List[str]
    sync_duration: float
    last_sync_token: Optional[str] = None

class AgentSDRCRMSync:
    """
    Comprehensive CRM synchronization system for AgentSDR
    Handles real-time bidirectional sync with major CRM platforms
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # CRM API credentials
        self.crm_credentials = {
            'salesforce': {
                'client_id': os.getenv('SALESFORCE_CLIENT_ID'),
                'client_secret': os.getenv('SALESFORCE_CLIENT_SECRET'),
                'username': os.getenv('SALESFORCE_USERNAME'),
                'password': os.getenv('SALESFORCE_PASSWORD'),
                'security_token': os.getenv('SALESFORCE_SECURITY_TOKEN')
            },
            'hubspot': {
                'api_key': os.getenv('HUBSPOT_API_KEY'),
                'access_token': os.getenv('HUBSPOT_ACCESS_TOKEN')
            },
            'zoho': {
                'client_id': os.getenv('ZOHO_CLIENT_ID'),
                'client_secret': os.getenv('ZOHO_CLIENT_SECRET'),
                'refresh_token': os.getenv('ZOHO_REFRESH_TOKEN')
            },
            'pipedrive': {
                'api_token': os.getenv('PIPEDRIVE_API_TOKEN'),
                'company_domain': os.getenv('PIPEDRIVE_COMPANY_DOMAIN')
            }
        }
        
        # Default field mappings for each CRM
        self.default_mappings = self._initialize_default_mappings()
    
    def setup_crm_integration(self, organization_id: str, crm_type: str, 
                             credentials: Dict, field_mappings: Optional[List[CRMMapping]] = None,
                             sync_settings: Optional[Dict] = None) -> bool:
        """
        Set up a new CRM integration for an organization
        """
        try:
            # Encrypt credentials
            encrypted_credentials = self._encrypt_credentials(credentials)
            
            # Use default mappings if none provided
            if not field_mappings:
                field_mappings = self.default_mappings.get(crm_type, [])
            
            # Default sync settings
            if not sync_settings:
                sync_settings = {
                    'sync_frequency': 15,  # minutes
                    'sync_direction': SyncDirection.BIDIRECTIONAL.value,
                    'auto_create_records': True,
                    'conflict_resolution': 'crm_wins',  # or 'agentsdr_wins', 'manual'
                    'batch_size': 100
                }
            
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            integration_data = {
                'organization_id': organization_id,
                'crm_type': crm_type,
                'integration_name': f"{crm_type.title()} Integration",
                'credentials': encrypted_credentials,
                'mapping_config': [
                    {
                        'agentsdr_field': mapping.agentsdr_field,
                        'crm_field': mapping.crm_field,
                        'field_type': mapping.field_type,
                        'transformation': mapping.transformation,
                        'is_required': mapping.is_required
                    }
                    for mapping in field_mappings
                ],
                'sync_settings': sync_settings,
                'status': SyncStatus.ACTIVE.value,
                'next_sync': datetime.now(timezone.utc).isoformat()
            }
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/crm_integrations",
                headers=headers,
                json=integration_data
            )
            
            if response.status_code == 201:
                print(f"CRM integration setup successful for {crm_type}")
                return True
            else:
                print(f"Error setting up CRM integration: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error setting up CRM integration: {e}")
            return False
    
    def sync_data(self, integration_id: str, sync_type: str = 'incremental') -> SyncResult:
        """
        Perform data synchronization for a specific integration
        """
        start_time = datetime.now()
        
        try:
            # Get integration configuration
            integration = self._get_integration_config(integration_id)
            if not integration:
                return SyncResult(False, 0, 0, 0, ["Integration not found"], 0)
            
            # Start sync logging
            sync_log_id = self._start_sync_log(integration_id, sync_type)
            
            # Get CRM connector
            connector = self._get_crm_connector(integration['crm_type'], integration['credentials'])
            if not connector:
                return SyncResult(False, 0, 0, 0, ["Failed to initialize CRM connector"], 0)
            
            results = []
            
            # Sync different data types
            sync_direction = integration['sync_settings'].get('sync_direction', 'bidirectional')
            
            if sync_direction in ['bidirectional', 'from_crm']:
                # Sync from CRM to AgentSDR
                lead_result = self._sync_leads_from_crm(connector, integration, sync_type)
                results.append(lead_result)
                
                opportunity_result = self._sync_opportunities_from_crm(connector, integration, sync_type)
                results.append(opportunity_result)
                
                activity_result = self._sync_activities_from_crm(connector, integration, sync_type)
                results.append(activity_result)
            
            if sync_direction in ['bidirectional', 'to_crm']:
                # Sync from AgentSDR to CRM
                lead_to_crm_result = self._sync_leads_to_crm(connector, integration, sync_type)
                results.append(lead_to_crm_result)
                
                opportunity_to_crm_result = self._sync_opportunities_to_crm(connector, integration, sync_type)
                results.append(opportunity_to_crm_result)
            
            # Aggregate results
            total_processed = sum(r.records_processed for r in results)
            total_success = sum(r.records_success for r in results)
            total_failed = sum(r.records_failed for r in results)
            all_errors = []
            for r in results:
                all_errors.extend(r.errors)
            
            sync_duration = (datetime.now() - start_time).total_seconds()
            
            final_result = SyncResult(
                success=total_failed == 0,
                records_processed=total_processed,
                records_success=total_success,
                records_failed=total_failed,
                errors=all_errors,
                sync_duration=sync_duration
            )
            
            # Update sync log
            self._complete_sync_log(sync_log_id, final_result)
            
            # Update integration next sync time
            self._update_next_sync_time(integration_id, integration['sync_settings']['sync_frequency'])
            
            return final_result
            
        except Exception as e:
            sync_duration = (datetime.now() - start_time).total_seconds()
            return SyncResult(False, 0, 0, 0, [str(e)], sync_duration)
    
    def _sync_leads_from_crm(self, connector: 'CRMConnector', integration: Dict, 
                            sync_type: str) -> SyncResult:
        """Sync leads from CRM to AgentSDR"""
        try:
            # Get last sync timestamp for incremental sync
            last_sync = None
            if sync_type == 'incremental':
                last_sync = integration.get('last_sync')
            
            # Fetch leads from CRM
            crm_leads = connector.get_leads(since=last_sync)
            
            if not crm_leads:
                return SyncResult(True, 0, 0, 0, [], 0)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for crm_lead in crm_leads:
                try:
                    # Transform CRM lead to AgentSDR format
                    agentsdr_lead = self._transform_lead_from_crm(
                        crm_lead, integration['mapping_config']
                    )
                    
                    # Check if lead already exists
                    existing_lead = self._find_existing_lead(agentsdr_lead)
                    
                    if existing_lead:
                        # Update existing lead
                        if self._update_lead(existing_lead['id'], agentsdr_lead):
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to update lead: {agentsdr_lead.get('email')}")
                    else:
                        # Create new lead
                        if self._create_lead(agentsdr_lead, integration['organization_id']):
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to create lead: {agentsdr_lead.get('email')}")
                            
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing lead: {str(e)}")
            
            return SyncResult(
                success=error_count == 0,
                records_processed=len(crm_leads),
                records_success=success_count,
                records_failed=error_count,
                errors=errors,
                sync_duration=0
            )
            
        except Exception as e:
            return SyncResult(False, 0, 0, 0, [str(e)], 0)
    
    def _sync_opportunities_from_crm(self, connector: 'CRMConnector', integration: Dict,
                                   sync_type: str) -> SyncResult:
        """Sync opportunities from CRM to AgentSDR"""
        try:
            last_sync = None
            if sync_type == 'incremental':
                last_sync = integration.get('last_sync')
            
            crm_opportunities = connector.get_opportunities(since=last_sync)
            
            if not crm_opportunities:
                return SyncResult(True, 0, 0, 0, [], 0)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for crm_opp in crm_opportunities:
                try:
                    agentsdr_opp = self._transform_opportunity_from_crm(
                        crm_opp, integration['mapping_config']
                    )
                    
                    existing_opp = self._find_existing_opportunity(agentsdr_opp)
                    
                    if existing_opp:
                        if self._update_opportunity(existing_opp['id'], agentsdr_opp):
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to update opportunity: {agentsdr_opp.get('name')}")
                    else:
                        if self._create_opportunity(agentsdr_opp, integration['organization_id']):
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to create opportunity: {agentsdr_opp.get('name')}")
                            
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing opportunity: {str(e)}")
            
            return SyncResult(
                success=error_count == 0,
                records_processed=len(crm_opportunities),
                records_success=success_count,
                records_failed=error_count,
                errors=errors,
                sync_duration=0
            )
            
        except Exception as e:
            return SyncResult(False, 0, 0, 0, [str(e)], 0)
    
    def _sync_activities_from_crm(self, connector: 'CRMConnector', integration: Dict,
                                sync_type: str) -> SyncResult:
        """Sync activities from CRM to AgentSDR"""
        try:
            last_sync = None
            if sync_type == 'incremental':
                last_sync = integration.get('last_sync')
            
            crm_activities = connector.get_activities(since=last_sync)
            
            if not crm_activities:
                return SyncResult(True, 0, 0, 0, [], 0)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for crm_activity in crm_activities:
                try:
                    agentsdr_activity = self._transform_activity_from_crm(
                        crm_activity, integration['mapping_config']
                    )
                    
                    if self._create_activity(agentsdr_activity, integration['organization_id']):
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Failed to create activity: {agentsdr_activity.get('subject')}")
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing activity: {str(e)}")
            
            return SyncResult(
                success=error_count == 0,
                records_processed=len(crm_activities),
                records_success=success_count,
                records_failed=error_count,
                errors=errors,
                sync_duration=0
            )
            
        except Exception as e:
            return SyncResult(False, 0, 0, 0, [str(e)], 0)
    
    def _sync_leads_to_crm(self, connector: 'CRMConnector', integration: Dict,
                          sync_type: str) -> SyncResult:
        """Sync leads from AgentSDR to CRM"""
        try:
            # Get leads that need to be synced to CRM
            leads_to_sync = self._get_leads_for_crm_sync(
                integration['organization_id'], 
                integration.get('last_sync') if sync_type == 'incremental' else None
            )
            
            if not leads_to_sync:
                return SyncResult(True, 0, 0, 0, [], 0)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for lead in leads_to_sync:
                try:
                    # Transform AgentSDR lead to CRM format
                    crm_lead = self._transform_lead_to_crm(lead, integration['mapping_config'])
                    
                    # Check if lead exists in CRM
                    existing_crm_lead = connector.find_lead_by_email(lead['email'])
                    
                    if existing_crm_lead:
                        # Update existing lead in CRM
                        if connector.update_lead(existing_crm_lead['id'], crm_lead):
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to update CRM lead: {lead['email']}")
                    else:
                        # Create new lead in CRM
                        crm_lead_id = connector.create_lead(crm_lead)
                        if crm_lead_id:
                            # Store CRM ID in AgentSDR lead for future reference
                            self._update_lead_crm_id(lead['id'], crm_lead_id)
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to create CRM lead: {lead['email']}")
                            
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error syncing lead to CRM: {str(e)}")
            
            return SyncResult(
                success=error_count == 0,
                records_processed=len(leads_to_sync),
                records_success=success_count,
                records_failed=error_count,
                errors=errors,
                sync_duration=0
            )
            
        except Exception as e:
            return SyncResult(False, 0, 0, 0, [str(e)], 0)
    
    def _sync_opportunities_to_crm(self, connector: 'CRMConnector', integration: Dict,
                                  sync_type: str) -> SyncResult:
        """Sync opportunities from AgentSDR to CRM"""
        try:
            opportunities_to_sync = self._get_opportunities_for_crm_sync(
                integration['organization_id'],
                integration.get('last_sync') if sync_type == 'incremental' else None
            )
            
            if not opportunities_to_sync:
                return SyncResult(True, 0, 0, 0, [], 0)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for opp in opportunities_to_sync:
                try:
                    crm_opp = self._transform_opportunity_to_crm(opp, integration['mapping_config'])
                    
                    existing_crm_opp = connector.find_opportunity_by_name(opp['name'])
                    
                    if existing_crm_opp:
                        if connector.update_opportunity(existing_crm_opp['id'], crm_opp):
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to update CRM opportunity: {opp['name']}")
                    else:
                        crm_opp_id = connector.create_opportunity(crm_opp)
                        if crm_opp_id:
                            self._update_opportunity_crm_id(opp['id'], crm_opp_id)
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"Failed to create CRM opportunity: {opp['name']}")
                            
                except Exception as e:
                    error_count += 1
                    errors.append(f"Error syncing opportunity to CRM: {str(e)}")
            
            return SyncResult(
                success=error_count == 0,
                records_processed=len(opportunities_to_sync),
                records_success=success_count,
                records_failed=error_count,
                errors=errors,
                sync_duration=0
            )
            
        except Exception as e:
            return SyncResult(False, 0, 0, 0, [str(e)], 0)
    
    def _get_crm_connector(self, crm_type: str, credentials: Dict) -> Optional['CRMConnector']:
        """Get appropriate CRM connector instance"""
        decrypted_creds = self._decrypt_credentials(credentials)
        
        if crm_type == CRMType.SALESFORCE.value:
            return SalesforceConnector(decrypted_creds)
        elif crm_type == CRMType.HUBSPOT.value:
            return HubSpotConnector(decrypted_creds)
        elif crm_type == CRMType.ZOHO.value:
            return ZohoConnector(decrypted_creds)
        elif crm_type == CRMType.PIPEDRIVE.value:
            return PipedriveConnector(decrypted_creds)
        else:
            return None
    
    def _initialize_default_mappings(self) -> Dict[str, List[CRMMapping]]:
        """Initialize default field mappings for each CRM"""
        return {
            'salesforce': [
                CRMMapping('first_name', 'FirstName', 'string', is_required=True),
                CRMMapping('last_name', 'LastName', 'string', is_required=True),
                CRMMapping('email', 'Email', 'email', is_required=True),
                CRMMapping('phone', 'Phone', 'phone'),
                CRMMapping('company', 'Company', 'string'),
                CRMMapping('job_title', 'Title', 'string'),
                CRMMapping('lead_source', 'LeadSource', 'string'),
                CRMMapping('status', 'Status', 'picklist'),
            ],
            'hubspot': [
                CRMMapping('first_name', 'firstname', 'string', is_required=True),
                CRMMapping('last_name', 'lastname', 'string', is_required=True),
                CRMMapping('email', 'email', 'string', is_required=True),
                CRMMapping('phone', 'phone', 'string'),
                CRMMapping('company', 'company', 'string'),
                CRMMapping('job_title', 'jobtitle', 'string'),
                CRMMapping('lead_source', 'hs_lead_status', 'enumeration'),
            ],
            'zoho': [
                CRMMapping('first_name', 'First_Name', 'string', is_required=True),
                CRMMapping('last_name', 'Last_Name', 'string', is_required=True),
                CRMMapping('email', 'Email', 'string', is_required=True),
                CRMMapping('phone', 'Phone', 'string'),
                CRMMapping('company', 'Company', 'string'),
                CRMMapping('job_title', 'Designation', 'string'),
                CRMMapping('lead_source', 'Lead_Source', 'picklist'),
            ],
            'pipedrive': [
                CRMMapping('first_name', 'first_name', 'varchar', is_required=True),
                CRMMapping('last_name', 'last_name', 'varchar', is_required=True),
                CRMMapping('email', 'email', 'varchar', is_required=True),
                CRMMapping('phone', 'phone', 'varchar'),
                CRMMapping('company', 'org_name', 'varchar'),
                CRMMapping('job_title', 'title', 'varchar'),
            ]
        }
    
    def _encrypt_credentials(self, credentials: Dict) -> str:
        """Encrypt CRM credentials for secure storage"""
        # In production, use proper encryption with a secret key
        # For now, using base64 encoding as placeholder
        credentials_json = json.dumps(credentials)
        encoded = base64.b64encode(credentials_json.encode()).decode()
        return encoded
    
    def _decrypt_credentials(self, encrypted_credentials: str) -> Dict:
        """Decrypt CRM credentials"""
        try:
            decoded = base64.b64decode(encrypted_credentials.encode()).decode()
            return json.loads(decoded)
        except:
            return {}
    
    def _get_integration_config(self, integration_id: str) -> Optional[Dict]:
        """Get CRM integration configuration"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/crm_integrations?id=eq.{integration_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            
            return None
        except Exception as e:
            print(f"Error getting integration config: {e}")
            return None
    
    # Additional helper methods for data transformation, logging, etc.
    # ... (implementing remaining methods for brevity)

# CRM Connector Base Class and Implementations
class CRMConnector:
    """Base class for CRM connectors"""
    
    def __init__(self, credentials: Dict):
        self.credentials = credentials
    
    def get_leads(self, since: Optional[str] = None) -> List[Dict]:
        raise NotImplementedError
    
    def get_opportunities(self, since: Optional[str] = None) -> List[Dict]:
        raise NotImplementedError
    
    def get_activities(self, since: Optional[str] = None) -> List[Dict]:
        raise NotImplementedError
    
    def create_lead(self, lead_data: Dict) -> Optional[str]:
        raise NotImplementedError
    
    def update_lead(self, lead_id: str, lead_data: Dict) -> bool:
        raise NotImplementedError
    
    def find_lead_by_email(self, email: str) -> Optional[Dict]:
        raise NotImplementedError

class SalesforceConnector(CRMConnector):
    """Salesforce CRM connector"""
    
    def __init__(self, credentials: Dict):
        super().__init__(credentials)
        self.access_token = None
        self.instance_url = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Salesforce"""
        try:
            auth_url = "https://login.salesforce.com/services/oauth2/token"
            
            auth_data = {
                'grant_type': 'password',
                'client_id': self.credentials['client_id'],
                'client_secret': self.credentials['client_secret'],
                'username': self.credentials['username'],
                'password': self.credentials['password'] + self.credentials.get('security_token', '')
            }
            
            response = requests.post(auth_url, data=auth_data)
            
            if response.status_code == 200:
                auth_response = response.json()
                self.access_token = auth_response['access_token']
                self.instance_url = auth_response['instance_url']
                print("Salesforce authentication successful")
            else:
                print(f"Salesforce authentication failed: {response.text}")
                
        except Exception as e:
            print(f"Error authenticating with Salesforce: {e}")
    
    def get_leads(self, since: Optional[str] = None) -> List[Dict]:
        """Get leads from Salesforce"""
        try:
            if not self.access_token:
                return []
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            query = "SELECT Id, FirstName, LastName, Email, Phone, Company, Title, LeadSource, Status, CreatedDate, LastModifiedDate FROM Lead"
            
            if since:
                query += f" WHERE LastModifiedDate > {since}"
            
            query += " ORDER BY LastModifiedDate DESC LIMIT 1000"
            
            response = requests.get(
                f"{self.instance_url}/services/data/v58.0/query",
                headers=headers,
                params={'q': query}
            )
            
            if response.status_code == 200:
                return response.json().get('records', [])
            else:
                print(f"Error fetching Salesforce leads: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error getting Salesforce leads: {e}")
            return []
    
    def create_lead(self, lead_data: Dict) -> Optional[str]:
        """Create lead in Salesforce"""
        try:
            if not self.access_token:
                return None
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.instance_url}/services/data/v58.0/sobjects/Lead",
                headers=headers,
                json=lead_data
            )
            
            if response.status_code == 201:
                return response.json().get('id')
            else:
                print(f"Error creating Salesforce lead: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating Salesforce lead: {e}")
            return None

class HubSpotConnector(CRMConnector):
    """HubSpot CRM connector"""
    
    def __init__(self, credentials: Dict):
        super().__init__(credentials)
        self.api_key = credentials.get('api_key')
        self.access_token = credentials.get('access_token')
    
    def get_leads(self, since: Optional[str] = None) -> List[Dict]:
        """Get contacts from HubSpot (HubSpot uses contacts instead of leads)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}' if self.access_token else None,
                'Content-Type': 'application/json'
            }
            
            if not self.access_token and self.api_key:
                # Use API key authentication
                url = f"https://api.hubapi.com/crm/v3/objects/contacts?hapikey={self.api_key}"
            else:
                url = "https://api.hubapi.com/crm/v3/objects/contacts"
            
            params = {
                'properties': 'firstname,lastname,email,phone,company,jobtitle,hs_lead_status,createdate,lastmodifieddate',
                'limit': 100
            }
            
            if since:
                # Convert since timestamp to HubSpot format
                params['filterGroups'] = json.dumps([{
                    'filters': [{
                        'propertyName': 'lastmodifieddate',
                        'operator': 'GTE',
                        'value': since
                    }]
                }])
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json().get('results', [])
            else:
                print(f"Error fetching HubSpot contacts: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error getting HubSpot contacts: {e}")
            return []

# Additional connector implementations for Zoho and Pipedrive would follow similar patterns

# Example usage and testing
if __name__ == "__main__":
    sync_manager = AgentSDRCRMSync()
    
    # Test integration setup
    test_org_id = "test-org-123"
    test_credentials = {
        'api_key': 'test-api-key',
        'access_token': 'test-access-token'
    }
    
    print("Setting up HubSpot integration...")
    success = sync_manager.setup_crm_integration(
        test_org_id, 
        CRMType.HUBSPOT.value, 
        test_credentials
    )
    
    if success:
        print("Integration setup successful")
    else:
        print("Integration setup failed")