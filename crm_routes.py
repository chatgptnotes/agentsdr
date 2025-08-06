"""
CRM API Routes for AgentSDR Platform
Provides endpoints for CRM integration and contact synchronization
"""

from flask import Blueprint, request, jsonify, g, redirect, session
from auth import login_required, admin_required
from crm_integration import crm_manager, initialize_crm, Contact
import sqlite3
from datetime import datetime
import json
import requests
import os
import secrets

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/api/crm/status', methods=['GET'])
@login_required
def get_crm_status():
    """Get CRM integration status"""
    try:
        # Import here to get the latest crm_manager state
        from crm_integration import crm_manager

        if not crm_manager:
            return jsonify({
                'connected': False,
                'crm_type': None,
                'message': 'No CRM integration configured'
            })

        # Test connection
        is_connected = crm_manager.authenticate()

        crm_type = crm_manager.__class__.__name__.replace('Integration', '').replace('CRM', '')

        return jsonify({
            'connected': is_connected,
            'crm_type': crm_type,
            'message': 'Connected' if is_connected else 'Connection failed'
        })

    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 500

@crm_bp.route('/api/crm/contacts/sync', methods=['POST'])
@login_required
def sync_crm_contacts():
    """Sync contacts from CRM to local database"""
    try:
        # Import here to get the latest crm_manager state
        from crm_integration import crm_manager

        if not crm_manager:
            return jsonify({'message': 'No CRM integration configured'}), 400
        
        # Get contacts from CRM
        crm_contacts = crm_manager.get_contacts(limit=500)
        
        if not crm_contacts:
            return jsonify({'message': 'No contacts found in CRM'}), 404
        
        # Get user's enterprise
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            return jsonify({'message': 'User not associated with enterprise'}), 400
        
        # Sync to local database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Create contacts table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                crm_id TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                status TEXT DEFAULT 'active',
                tags TEXT,
                enterprise_id TEXT,
                voice_agent_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enterprise_id) REFERENCES enterprises(id)
            )
        ''')
        
        synced_count = 0
        updated_count = 0
        
        for crm_contact in crm_contacts:
            # Check if contact already exists
            cursor.execute('''
                SELECT id FROM contacts 
                WHERE crm_id = ? AND enterprise_id = ?
            ''', (crm_contact.id, enterprise_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing contact
                cursor.execute('''
                    UPDATE contacts 
                    SET first_name = ?, last_name = ?, email = ?, phone = ?, 
                        company = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE crm_id = ? AND enterprise_id = ?
                ''', (
                    crm_contact.first_name, crm_contact.last_name,
                    crm_contact.email, crm_contact.phone,
                    crm_contact.company, crm_contact.status,
                    crm_contact.id, enterprise_id
                ))
                updated_count += 1
            else:
                # Create new contact
                contact_id = f"contact-{crm_contact.id}"
                cursor.execute('''
                    INSERT INTO contacts 
                    (id, crm_id, first_name, last_name, email, phone, company, 
                     status, enterprise_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    contact_id, crm_contact.id, crm_contact.first_name,
                    crm_contact.last_name, crm_contact.email, crm_contact.phone,
                    crm_contact.company, crm_contact.status, enterprise_id
                ))
                synced_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Contacts synced successfully',
            'synced': synced_count,
            'updated': updated_count,
            'total': len(crm_contacts)
        })
        
    except Exception as e:
        return jsonify({'message': f'Sync failed: {str(e)}'}), 500

@crm_bp.route('/api/crm/contacts', methods=['GET'])
@login_required
def get_synced_contacts():
    """Get synced contacts from local database"""
    try:
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            return jsonify({'message': 'User not associated with enterprise'}), 400
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, crm_id, first_name, last_name, email, phone, company, 
                   status, voice_agent_id, created_at, updated_at
            FROM contacts 
            WHERE enterprise_id = ?
            ORDER BY updated_at DESC
        ''', (enterprise_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        contacts = []
        for row in rows:
            contacts.append({
                'id': row[0],
                'crm_id': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'email': row[4],
                'phone': row[5],
                'company': row[6],
                'status': row[7],
                'voice_agent_id': row[8],
                'created_at': row[9],
                'updated_at': row[10]
            })
        
        return jsonify({
            'contacts': contacts,
            'total': len(contacts)
        })
        
    except Exception as e:
        return jsonify({'message': f'Failed to get contacts: {str(e)}'}), 500

@crm_bp.route('/api/crm/contacts/<contact_id>/assign-agent', methods=['POST'])
@login_required
def assign_contact_to_agent(contact_id):
    """Assign a contact to a voice agent"""
    try:
        data = request.get_json()
        agent_id = data.get('agent_id')
        
        if not agent_id:
            return jsonify({'message': 'Agent ID is required'}), 400
        
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            return jsonify({'message': 'User not associated with enterprise'}), 400
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verify contact belongs to enterprise
        cursor.execute('''
            SELECT id FROM contacts 
            WHERE id = ? AND enterprise_id = ?
        ''', (contact_id, enterprise_id))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'message': 'Contact not found'}), 404
        
        # Verify agent belongs to enterprise
        cursor.execute('''
            SELECT id FROM voice_agents 
            WHERE id = ? AND enterprise_id = ?
        ''', (agent_id, enterprise_id))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'message': 'Voice agent not found'}), 404
        
        # Assign contact to agent
        cursor.execute('''
            UPDATE contacts 
            SET voice_agent_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (agent_id, contact_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Contact assigned to voice agent successfully'})
        
    except Exception as e:
        return jsonify({'message': f'Assignment failed: {str(e)}'}), 500

@crm_bp.route('/api/crm/sync-call-result', methods=['POST'])
@login_required
def sync_call_result_to_crm():
    """Sync call results back to CRM"""
    try:
        # Import here to get the latest crm_manager state
        from crm_integration import crm_manager

        if not crm_manager:
            return jsonify({'message': 'No CRM integration configured'}), 400
        
        data = request.get_json()
        contact_id = data.get('contact_id')
        call_data = data.get('call_data', {})
        
        if not contact_id:
            return jsonify({'message': 'Contact ID is required'}), 400
        
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            return jsonify({'message': 'User not associated with enterprise'}), 400
        
        # Get contact's CRM ID
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT crm_id FROM contacts 
            WHERE id = ? AND enterprise_id = ?
        ''', (contact_id, enterprise_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return jsonify({'message': 'Contact not found or not synced from CRM'}), 404
        
        crm_contact_id = result[0]
        
        # Sync to CRM
        success = crm_manager.sync_call_results(crm_contact_id, call_data)
        
        if success:
            return jsonify({'message': 'Call results synced to CRM successfully'})
        else:
            return jsonify({'message': 'Failed to sync call results to CRM'}), 500
        
    except Exception as e:
        return jsonify({'message': f'Sync failed: {str(e)}'}), 500

@crm_bp.route('/api/crm/configure', methods=['POST'])
@admin_required
def configure_crm():
    """Configure CRM integration (Admin only)"""
    try:
        data = request.get_json()
        crm_type = data.get('crm_type')
        
        if not crm_type:
            return jsonify({'message': 'CRM type is required'}), 400
        
        # Initialize CRM with new configuration
        success = initialize_crm(crm_type)
        
        if success:
            return jsonify({
                'message': f'{crm_type.title()} CRM configured successfully',
                'crm_type': crm_type
            })
        else:
            return jsonify({
                'message': f'Failed to configure {crm_type.title()} CRM'
            }), 500
        
    except Exception as e:
        return jsonify({'message': f'Configuration failed: {str(e)}'}), 500

# HubSpot OAuth Routes
@crm_bp.route('/api/crm/hubspot/auth', methods=['GET'])
@login_required
def hubspot_auth():
    """Initiate HubSpot OAuth flow"""
    try:
        client_id = os.getenv('HUBSPOT_CLIENT_ID')
        redirect_uri = os.getenv('HUBSPOT_REDIRECT_URI')

        if not client_id or not redirect_uri:
            return jsonify({'error': 'HubSpot OAuth not configured'}), 400

        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        session['hubspot_oauth_state'] = state
        session['user_id'] = g.user_id  # Store user ID for callback

        # HubSpot OAuth URL
        scopes = 'crm.objects.contacts.read crm.objects.contacts.write crm.objects.companies.read crm.objects.notes.write'
        auth_url = (
            f"https://app.hubspot.com/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scopes}"
            f"&state={state}"
        )

        return redirect(auth_url)

    except Exception as e:
        return jsonify({'error': f'OAuth initiation failed: {str(e)}'}), 500

@crm_bp.route('/api/crm/hubspot/callback', methods=['GET'])
def hubspot_callback():
    """Handle HubSpot OAuth callback"""
    try:
        # Get authorization code and state
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        if error:
            return jsonify({'error': f'OAuth error: {error}'}), 400

        if not code:
            return jsonify({'error': 'No authorization code received'}), 400

        # Verify state parameter
        if not session.get('hubspot_oauth_state') or session['hubspot_oauth_state'] != state:
            return jsonify({'error': 'Invalid state parameter'}), 400

        # Exchange code for access token
        client_id = os.getenv('HUBSPOT_CLIENT_ID')
        client_secret = os.getenv('HUBSPOT_CLIENT_SECRET')
        redirect_uri = os.getenv('HUBSPOT_REDIRECT_URI')

        token_data = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code
        }

        token_response = requests.post(
            'https://api.hubapi.com/oauth/v1/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if token_response.status_code != 200:
            return jsonify({'error': 'Failed to exchange code for token'}), 400

        token_info = token_response.json()
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')
        expires_in = token_info.get('expires_in')

        # Store tokens in database (you may want to encrypt these)
        user_id = session.get('user_id')
        if user_id:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            # Store or update HubSpot tokens
            cursor.execute('''
                INSERT OR REPLACE INTO crm_tokens
                (user_id, crm_type, access_token, refresh_token, expires_at, created_at)
                VALUES (?, ?, ?, ?, datetime('now', '+' || ? || ' seconds'), datetime('now'))
            ''', (user_id, 'hubspot', access_token, refresh_token, expires_in))

            conn.commit()
            conn.close()

        # Clear session state
        session.pop('hubspot_oauth_state', None)
        session.pop('user_id', None)

        # Redirect to dashboard with success message
        return redirect('/dashboard.html?hubspot_connected=true')

    except Exception as e:
        return jsonify({'error': f'OAuth callback failed: {str(e)}'}), 500

@crm_bp.route('/api/crm/hubspot/disconnect', methods=['POST'])
@login_required
def hubspot_disconnect():
    """Disconnect HubSpot integration"""
    try:
        user_id = g.user_id

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Remove stored tokens
        cursor.execute('DELETE FROM crm_tokens WHERE user_id = ? AND crm_type = ?', (user_id, 'hubspot'))

        conn.commit()
        conn.close()

        return jsonify({'message': 'HubSpot disconnected successfully'})

    except Exception as e:
        return jsonify({'error': f'Disconnect failed: {str(e)}'}), 500

@crm_bp.route('/api/crm/hubspot/sync-contacts', methods=['POST'])
@login_required
def sync_hubspot_contacts():
    """Sync contacts from HubSpot to AgentSDR"""
    try:
        user_id = g.user_id

        # Get HubSpot access token
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT access_token FROM crm_tokens
            WHERE user_id = ? AND crm_type = 'hubspot'
            AND expires_at > datetime('now')
        ''', (user_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'HubSpot not connected or token expired'}), 400

        access_token = result[0]

        # Fetch contacts from HubSpot
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Get contacts from HubSpot API
        hubspot_response = requests.get(
            'https://api.hubapi.com/crm/v3/objects/contacts',
            headers=headers,
            params={
                'limit': 100,
                'properties': 'firstname,lastname,email,phone,company,lifecyclestage'
            }
        )

        if hubspot_response.status_code != 200:
            conn.close()
            return jsonify({'error': 'Failed to fetch contacts from HubSpot'}), 400

        hubspot_contacts = hubspot_response.json().get('results', [])

        # Get user's enterprise_id
        cursor.execute('SELECT enterprise_id FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        enterprise_id = user_data[0] if user_data else None

        # Create contacts table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                crm_id TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                status TEXT DEFAULT 'active',
                source TEXT DEFAULT 'hubspot',
                tags TEXT,
                enterprise_id TEXT,
                voice_agent_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enterprise_id) REFERENCES enterprises(id)
            )
        ''')

        synced_count = 0
        updated_count = 0

        for contact in hubspot_contacts:
            properties = contact.get('properties', {})
            hubspot_id = contact.get('id')

            # Extract contact data
            first_name = properties.get('firstname', '')
            last_name = properties.get('lastname', '')
            email = properties.get('email', '')
            phone = properties.get('phone', '')
            company = properties.get('company', '')
            lifecycle_stage = properties.get('lifecyclestage', '')

            # Skip contacts without email
            if not email:
                continue

            # Check if contact already exists
            cursor.execute('''
                SELECT id FROM contacts
                WHERE crm_id = ? OR email = ?
            ''', (hubspot_id, email))

            existing_contact = cursor.fetchone()

            if existing_contact:
                # Update existing contact
                cursor.execute('''
                    UPDATE contacts
                    SET first_name = ?, last_name = ?, email = ?, phone = ?,
                        company = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (first_name, last_name, email, phone, company, existing_contact[0]))
                updated_count += 1
            else:
                # Create new contact
                contact_id = f"contact-{secrets.token_hex(8)}"
                cursor.execute('''
                    INSERT INTO contacts
                    (id, crm_id, first_name, last_name, email, phone, company,
                     source, enterprise_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (contact_id, hubspot_id, first_name, last_name, email,
                      phone, company, 'hubspot', enterprise_id, 'active'))
                synced_count += 1

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Contacts synced successfully',
            'synced_count': synced_count,
            'updated_count': updated_count,
            'total_processed': len(hubspot_contacts)
        })

    except Exception as e:
        return jsonify({'error': f'Contact sync failed: {str(e)}'}), 500

@crm_bp.route('/api/crm/contacts', methods=['GET'])
@login_required
def get_crm_contacts():
    """Get all CRM contacts for the user"""
    try:
        user_id = g.user_id

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Get user's enterprise_id
        cursor.execute('SELECT enterprise_id FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        enterprise_id = user_data[0] if user_data else None

        # Get contacts
        cursor.execute('''
            SELECT id, crm_id, first_name, last_name, email, phone, company,
                   source, status, created_at, updated_at
            FROM contacts
            WHERE enterprise_id = ? OR enterprise_id IS NULL
            ORDER BY created_at DESC
        ''', (enterprise_id,))

        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                'id': row[0],
                'crm_id': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'email': row[4],
                'phone': row[5],
                'company': row[6],
                'source': row[7],
                'status': row[8],
                'created_at': row[9],
                'updated_at': row[10]
            })

        conn.close()

        return jsonify({
            'contacts': contacts,
            'total_count': len(contacts)
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get contacts: {str(e)}'}), 500

# Initialize CRM on module load
try:
    initialize_crm()
except Exception as e:
    print(f"Warning: CRM initialization failed: {e}")
