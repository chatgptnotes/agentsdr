#!/usr/bin/env python3
"""
AgentSDR Deployment Setup Script
Automates the initial setup and configuration of AgentSDR for production
"""

import os
import sys
import json
import requests
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import secrets

class AgentSDRDeploymentSetup:
    """Automates AgentSDR deployment setup and configuration"""
    
    def __init__(self):
        self.config = {}
        self.setup_log = []
        
    def log(self, message: str, success: bool = True):
        """Log setup progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅" if success else "❌"
        log_entry = f"{timestamp} {status} {message}"
        print(log_entry)
        self.setup_log.append(log_entry)
    
    def generate_secret_key(self) -> str:
        """Generate a secure secret key for Flask"""
        return secrets.token_urlsafe(32)
    
    def validate_environment_setup(self) -> bool:
        """Validate that all required environment variables are set"""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_KEY',
            'SUPABASE_ANON_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log(f"Missing required environment variables: {', '.join(missing_vars)}", False)
            return False
        
        self.log("Environment variables validation passed")
        return True
    
    def test_supabase_connection(self) -> bool:
        """Test connection to Supabase database"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Test with a simple request
            response = requests.get(
                f"{supabase_url}/rest/v1/organizations?limit=1",
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 404]:  # 404 is ok if no data exists
                self.log("Supabase connection successful")
                return True
            else:
                self.log(f"Supabase connection failed: {response.status_code}", False)
                return False
                
        except Exception as e:
            self.log(f"Supabase connection error: {e}", False)
            return False
    
    def verify_database_schema(self) -> bool:
        """Verify that all required tables exist"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            required_tables = [
                'organizations', 'users', 'leads', 'opportunities', 
                'activities', 'daily_briefings', 'proposals'
            ]
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            missing_tables = []
            for table in required_tables:
                try:
                    response = requests.get(
                        f"{supabase_url}/rest/v1/{table}?limit=1",
                        headers=headers,
                        timeout=5
                    )
                    if response.status_code not in [200, 404]:
                        missing_tables.append(table)
                except:
                    missing_tables.append(table)
            
            if missing_tables:
                self.log(f"Missing database tables: {', '.join(missing_tables)}", False)
                self.log("Please run the agentsdr_schema.sql file in Supabase SQL Editor", False)
                return False
            
            self.log("Database schema verification passed")
            return True
            
        except Exception as e:
            self.log(f"Database schema verification error: {e}", False)
            return False
    
    def test_ai_integration(self) -> bool:
        """Test OpenAI API integration"""
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            self.log("OpenAI API key not configured - AI features will be disabled")
            return True  # Not required for basic functionality
        
        try:
            import openai
            openai.api_key = openai_key
            
            # Test with a simple completion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            self.log("OpenAI API connection successful")
            return True
            
        except Exception as e:
            self.log(f"OpenAI API test failed: {e}", False)
            return False
    
    def create_initial_organization(self) -> bool:
        """Create initial organization and admin user"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
            
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Check if organization already exists
            response = requests.get(
                f"{supabase_url}/rest/v1/organizations?limit=1",
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                self.log("Organization already exists - skipping creation")
                return True
            
            # Create organization
            org_data = {
                'name': 'AgentSDR Demo Organization',
                'description': 'Initial organization for AgentSDR deployment',
                'status': 'active',
                'plan_type': 'enterprise'
            }
            
            response = requests.post(
                f"{supabase_url}/rest/v1/organizations",
                headers=headers,
                json=org_data
            )
            
            if response.status_code == 201:
                self.log("Initial organization created successfully")
                
                # Get the created organization ID
                org_response = requests.get(
                    f"{supabase_url}/rest/v1/organizations?name=eq.AgentSDR Demo Organization",
                    headers=headers
                )
                
                if org_response.status_code == 200:
                    org_data = org_response.json()[0]
                    org_id = org_data['id']
                    
                    # Create admin user
                    user_data = {
                        'email': 'admin@agentsdr.com',
                        'name': 'AgentSDR Admin',
                        'role': 'super_admin',
                        'organization_id': org_id,
                        'status': 'active'
                    }
                    
                    user_response = requests.post(
                        f"{supabase_url}/rest/v1/users",
                        headers=headers,
                        json=user_data
                    )
                    
                    if user_response.status_code == 201:
                        self.log("Admin user created successfully")
                        self.log("Login credentials: admin@agentsdr.com")
                        return True
                    else:
                        self.log(f"Failed to create admin user: {user_response.text}", False)
                        return False
                else:
                    self.log("Failed to retrieve created organization", False)
                    return False
            else:
                self.log(f"Failed to create organization: {response.text}", False)
                return False
                
        except Exception as e:
            self.log(f"Error creating initial data: {e}", False)
            return False
    
    def install_dependencies(self) -> bool:
        """Install required Python dependencies"""
        try:
            self.log("Installing Python dependencies...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log("Dependencies installed successfully")
                return True
            else:
                self.log(f"Failed to install dependencies: {result.stderr}", False)
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Dependency installation timed out", False)
            return False
        except Exception as e:
            self.log(f"Error installing dependencies: {e}", False)
            return False
    
    def create_production_env_file(self) -> bool:
        """Create production environment file with secure defaults"""
        try:
            if os.path.exists('.env.production'):
                self.log("Production environment file already exists")
                return True
            
            # Generate secure secret key
            secret_key = self.generate_secret_key()
            
            env_content = f"""# AgentSDR Production Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Supabase Configuration (Required)
SUPABASE_URL={os.getenv('SUPABASE_URL', 'https://your-project-id.supabase.co')}
SUPABASE_SERVICE_KEY={os.getenv('SUPABASE_SERVICE_KEY', 'your-service-role-key')}
SUPABASE_ANON_KEY={os.getenv('SUPABASE_ANON_KEY', 'your-anon-key')}

# Flask Configuration
SECRET_KEY={secret_key}
FLASK_ENV=production
FLASK_DEBUG=False

# AI and Intelligence APIs (Optional but recommended)
OPENAI_API_KEY={os.getenv('OPENAI_API_KEY', 'your-openai-api-key')}
ANTHROPIC_API_KEY={os.getenv('ANTHROPIC_API_KEY', 'your-anthropic-key')}

# WhatsApp Business API (Optional)
WHATSAPP_BUSINESS_API_TOKEN={os.getenv('WHATSAPP_BUSINESS_API_TOKEN', 'your-whatsapp-token')}
WHATSAPP_PHONE_NUMBER_ID={os.getenv('WHATSAPP_PHONE_NUMBER_ID', 'your-phone-number-id')}
WHATSAPP_WEBHOOK_VERIFY_TOKEN={os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'your-webhook-verify-token')}

# CRM Integration APIs (Configure as needed)
SALESFORCE_CLIENT_ID={os.getenv('SALESFORCE_CLIENT_ID', 'your-salesforce-client-id')}
SALESFORCE_CLIENT_SECRET={os.getenv('SALESFORCE_CLIENT_SECRET', 'your-salesforce-client-secret')}
HUBSPOT_API_KEY={os.getenv('HUBSPOT_API_KEY', 'your-hubspot-api-key')}
ZOHO_CLIENT_ID={os.getenv('ZOHO_CLIENT_ID', 'your-zoho-client-id')}
ZOHO_CLIENT_SECRET={os.getenv('ZOHO_CLIENT_SECRET', 'your-zoho-client-secret')}
PIPEDRIVE_API_TOKEN={os.getenv('PIPEDRIVE_API_TOKEN', 'your-pipedrive-token')}

# Email Service APIs (Optional)
SENDGRID_API_KEY={os.getenv('SENDGRID_API_KEY', 'your-sendgrid-api-key')}
AWS_SES_ACCESS_KEY={os.getenv('AWS_SES_ACCESS_KEY', 'your-aws-ses-access-key')}
AWS_SES_SECRET_KEY={os.getenv('AWS_SES_SECRET_KEY', 'your-aws-ses-secret-key')}
"""
            
            with open('.env.production', 'w') as f:
                f.write(env_content)
            
            # Set secure permissions
            os.chmod('.env.production', 0o600)
            
            self.log("Production environment file created successfully")
            self.log("Please update .env.production with your actual API keys")
            return True
            
        except Exception as e:
            self.log(f"Error creating production environment file: {e}", False)
            return False
    
    def run_health_check(self) -> bool:
        """Run comprehensive health check"""
        try:
            self.log("Running health check...")
            
            # Test imports
            modules_to_test = [
                'briefing_engine',
                'followup_manager',
                'crm_sync',
                'proposal_generator',
                'opportunity_intelligence',
                'meeting_prep'
            ]
            
            failed_imports = []
            for module in modules_to_test:
                try:
                    __import__(module)
                    self.log(f"✅ {module} import successful")
                except Exception as e:
                    self.log(f"❌ {module} import failed: {e}", False)
                    failed_imports.append(module)
            
            if failed_imports:
                self.log(f"Failed module imports: {', '.join(failed_imports)}", False)
                return False
            
            self.log("All module imports successful")
            return True
            
        except Exception as e:
            self.log(f"Health check error: {e}", False)
            return False
    
    def generate_deployment_report(self) -> str:
        """Generate deployment setup report"""
        report = f"""
# AgentSDR Deployment Setup Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Setup Log:
"""
        for entry in self.setup_log:
            report += f"{entry}\n"
        
        report += f"""
## Configuration Summary:
- Supabase URL: {os.getenv('SUPABASE_URL', 'Not configured')}
- OpenAI API: {'Configured' if os.getenv('OPENAI_API_KEY') else 'Not configured'}
- WhatsApp API: {'Configured' if os.getenv('WHATSAPP_BUSINESS_API_TOKEN') else 'Not configured'}

## Next Steps:
1. Update .env.production with your actual API keys
2. Deploy to your chosen hosting platform
3. Configure webhooks for WhatsApp (if using)
4. Set up CRM integrations
5. Create user accounts for your sales team
6. Run production testing

## Useful Commands:
```bash
# Start development server
python main.py

# Test database connection
python test_connection.py

# Run health check
python deploy_setup.py --health-check
```
"""
        return report
    
    def run_full_setup(self) -> bool:
        """Run complete deployment setup process"""
        self.log("Starting AgentSDR deployment setup...")
        
        steps = [
            ("Installing dependencies", self.install_dependencies),
            ("Validating environment", self.validate_environment_setup),
            ("Testing Supabase connection", self.test_supabase_connection),
            ("Verifying database schema", self.verify_database_schema),
            ("Testing AI integration", self.test_ai_integration),
            ("Creating initial organization", self.create_initial_organization),
            ("Creating production environment file", self.create_production_env_file),
            ("Running health check", self.run_health_check)
        ]
        
        failed_steps = []
        for step_name, step_function in steps:
            self.log(f"Running: {step_name}")
            if not step_function():
                failed_steps.append(step_name)
        
        if failed_steps:
            self.log(f"Setup completed with errors in: {', '.join(failed_steps)}", False)
            return False
        else:
            self.log("🎉 AgentSDR setup completed successfully!")
            return True

def main():
    """Main deployment setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AgentSDR Deployment Setup')
    parser.add_argument('--health-check', action='store_true', help='Run health check only')
    parser.add_argument('--create-env', action='store_true', help='Create production environment file only')
    parser.add_argument('--test-db', action='store_true', help='Test database connection only')
    
    args = parser.parse_args()
    
    setup = AgentSDRDeploymentSetup()
    
    if args.health_check:
        setup.run_health_check()
    elif args.create_env:
        setup.create_production_env_file()
    elif args.test_db:
        setup.test_supabase_connection()
        setup.verify_database_schema()
    else:
        # Run full setup
        success = setup.run_full_setup()
        
        # Generate report
        report = setup.generate_deployment_report()
        
        # Save report
        with open('deployment_report.md', 'w') as f:
            f.write(report)
        
        print("\n" + "="*50)
        print("Deployment report saved to: deployment_report.md")
        
        if success:
            print("\n🚀 AgentSDR is ready for production!")
            print("Next steps:")
            print("1. Update .env.production with your API keys")
            print("2. Deploy to your hosting platform")
            print("3. Access your dashboard at: http://localhost:8000")
        else:
            print("\n⚠️  Setup completed with some errors.")
            print("Please check the deployment report for details.")
        
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())