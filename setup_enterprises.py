#!/usr/bin/env python3
"""
Setup enterprises for AgentSDR SQLite database
This script creates the enterprises table and associates existing users with enterprises
"""

import sqlite3
import uuid
from datetime import datetime

def setup_enterprises():
    """Create enterprises table and associate users with enterprises"""
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # Create enterprises table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enterprises (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'business',
                contact_email TEXT,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
                owner_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        ''')
        
        # Create sample enterprises
        enterprises = [
            {
                'id': 'ent-bhashai-001',
                'name': 'BhashAI Technologies',
                'description': 'AI-powered voice agent solutions',
                'type': 'technology',
                'contact_email': 'contact@bhashai.com',
                'status': 'active',
                'owner_id': 'admin-001'
            },
            {
                'id': 'ent-demo-002', 
                'name': 'Demo Enterprise',
                'description': 'Demo enterprise for testing',
                'type': 'demo',
                'contact_email': 'demo@bhashai.com',
                'status': 'active',
                'owner_id': 'manager-001'
            }
        ]
        
        # Insert enterprises
        for ent in enterprises:
            cursor.execute('''
                INSERT OR REPLACE INTO enterprises 
                (id, name, description, type, contact_email, status, owner_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (ent['id'], ent['name'], ent['description'], ent['type'], 
                  ent['contact_email'], ent['status'], ent['owner_id']))
        
        # Associate users with enterprises
        user_enterprise_mapping = [
            ('admin-001', 'ent-bhashai-001'),
            ('manager-001', 'ent-bhashai-001'), 
            ('user-001', 'ent-bhashai-001'),
            ('user-002', 'ent-demo-002'),
            ('user-db9e5abb0f5d426f', 'ent-demo-002')
        ]
        
        # Update users with enterprise_id
        for user_id, enterprise_id in user_enterprise_mapping:
            cursor.execute('''
                UPDATE users 
                SET enterprise_id = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (enterprise_id, user_id))
        
        conn.commit()
        
        # Verify the setup
        print("✅ Enterprises created successfully!")
        cursor.execute("SELECT id, name, status FROM enterprises")
        enterprises = cursor.fetchall()
        for ent in enterprises:
            print(f"   📊 {ent[1]} ({ent[0]}) - {ent[2]}")
        
        print("\n✅ Users associated with enterprises:")
        cursor.execute("""
            SELECT u.email, u.role, u.enterprise_id, e.name 
            FROM users u 
            LEFT JOIN enterprises e ON u.enterprise_id = e.id
        """)
        users = cursor.fetchall()
        for user in users:
            enterprise_name = user[3] if user[3] else "No Enterprise"
            print(f"   👤 {user[0]} ({user[1]}) -> {enterprise_name}")
            
    except Exception as e:
        print(f"❌ Error setting up enterprises: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_enterprises()
