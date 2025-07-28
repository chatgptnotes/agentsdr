# AgentSDR Production Deployment Guide

This guide will walk you through deploying AgentSDR to production and configuring all necessary integrations.

## 🚀 Quick Start Checklist

- [ ] Supabase project setup
- [ ] Environment variables configured
- [ ] Database schema deployed
- [ ] API integrations configured
- [ ] Flask application deployed
- [ ] WhatsApp Business API setup
- [ ] CRM integrations tested
- [ ] User accounts created
- [ ] Production testing completed

## 📋 Prerequisites

### Required Accounts & Services:
1. **Supabase Account** - Database and authentication
2. **OpenAI Account** - AI insights and content generation
3. **WhatsApp Business API** - Mobile notifications
4. **CRM Platform** - Salesforce/HubSpot/Zoho/Pipedrive
5. **Email Service** - SendGrid or AWS SES
6. **Hosting Platform** - Railway, Heroku, or VPS

### Required Skills:
- Basic command line usage
- Environment variable configuration
- Database management (Supabase)

## 🗄️ Step 1: Database Setup

### 1.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Choose region closest to your users
4. Note down your project URL and keys

### 1.2 Deploy Database Schema
```bash
# In Supabase SQL Editor, run:
# 1. Copy content from agentsdr_schema.sql
# 2. Paste and execute in SQL Editor
# 3. Verify all tables are created successfully
```

### 1.3 Enable Row Level Security
```sql
-- Verify RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND rowsecurity = true;
```

### 1.4 Create Initial Data
```sql
-- Create your organization
INSERT INTO organizations (name, description, status, plan_type) 
VALUES ('Your Company Name', 'Main sales organization', 'active', 'enterprise');

-- Create admin user
INSERT INTO users (email, name, role, organization_id, status) 
VALUES (
    'admin@yourcompany.com', 
    'Admin User', 
    'super_admin', 
    (SELECT id FROM organizations WHERE name = 'Your Company Name'),
    'active'
);
```

## ⚙️ Step 2: Environment Configuration

### 2.1 Create Production Environment File
```bash
cp .env.example .env.production
```

### 2.2 Configure Environment Variables
```bash
# AgentSDR Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
SECRET_KEY=your-strong-secret-key-here

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# AI and Intelligence APIs
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-key

# WhatsApp Business API
WHATSAPP_BUSINESS_API_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-webhook-verify-token

# CRM Integration APIs
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
HUBSPOT_API_KEY=your-hubspot-api-key
ZOHO_CLIENT_ID=your-zoho-client-id
ZOHO_CLIENT_SECRET=your-zoho-client-secret
PIPEDRIVE_API_TOKEN=your-pipedrive-token

# Email Service APIs
SENDGRID_API_KEY=your-sendgrid-api-key
AWS_SES_ACCESS_KEY=your-aws-ses-access-key
AWS_SES_SECRET_KEY=your-aws-ses-secret-key
```

## 🤖 Step 3: AI Integration Setup

### 3.1 OpenAI API Setup
1. Visit [platform.openai.com](https://platform.openai.com)
2. Create API key with appropriate usage limits
3. Add billing information for production use
4. Test connection:
```bash
python -c "
import openai
openai.api_key = 'your-api-key'
response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Hello AgentSDR!'}]
)
print('OpenAI connection successful!')
"
```

### 3.2 Configure AI Usage Limits
```python
# In briefing_engine.py, adjust model usage:
DAILY_AI_REQUEST_LIMIT = 1000  # Adjust based on your plan
BRIEFING_MODEL = "gpt-3.5-turbo"  # or "gpt-4" for better results
INSIGHT_MODEL = "gpt-3.5-turbo"
```

## 📱 Step 4: WhatsApp Business API Setup

### 4.1 WhatsApp Business Account
1. Apply for WhatsApp Business API access
2. Get approved and receive credentials
3. Set up webhook endpoint: `https://your-domain.com/webhook/whatsapp`

### 4.2 Configure Webhook
```python
# Add to main.py
@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        # Webhook verification
        verify_token = request.args.get('hub.verify_token')
        if verify_token == os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return 'Invalid verify token', 403
    
    # Handle incoming messages (optional)
    return 'OK', 200
```

### 4.3 Test WhatsApp Integration
```bash
python -c "
from briefing_engine import AgentSDRBriefingEngine
engine = AgentSDRBriefingEngine()
# Test sending a message
result = engine.send_whatsapp_briefing('+1234567890', test_briefing)
print('WhatsApp test:', 'Success' if result else 'Failed')
"
```

## 🔗 Step 5: CRM Integration Setup

### 5.1 Salesforce Integration
```bash
# Test Salesforce connection
python -c "
from crm_sync import AgentSDRCRMSync
sync = AgentSDRCRMSync()
success = sync.setup_crm_integration(
    'your-org-id',
    'salesforce',
    {
        'client_id': 'your-client-id',
        'client_secret': 'your-client-secret',
        'username': 'your-username',
        'password': 'your-password',
        'security_token': 'your-token'
    }
)
print('Salesforce setup:', 'Success' if success else 'Failed')
"
```

### 5.2 HubSpot Integration
```bash
# Test HubSpot connection
python -c "
from crm_sync import AgentSDRCRMSync
sync = AgentSDRCRMSync()
success = sync.setup_crm_integration(
    'your-org-id',
    'hubspot',
    {
        'api_key': 'your-hubspot-api-key'
    }
)
print('HubSpot setup:', 'Success' if success else 'Failed')
"
```

## 🚢 Step 6: Application Deployment

### 6.1 Railway Deployment (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### 6.2 Heroku Deployment
```bash
# Install Heroku CLI
# Create Procfile (already included)
heroku create your-agentsdr-app
heroku config:set FLASK_ENV=production
# Add all environment variables
heroku config:set SUPABASE_URL=your-url
# ... (add all env vars)
git push heroku agentsdr-clean:main
```

### 6.3 Docker Deployment
```bash
# Build and run with Docker
docker build -t agentsdr .
docker run -p 5000:5000 --env-file .env.production agentsdr
```

## 🧪 Step 7: Production Testing

### 7.1 Health Check Endpoints
```bash
# Test basic functionality
curl https://your-domain.com/health
curl https://your-domain.com/api/test
```

### 7.2 Core Feature Testing
```bash
# Test database connection
python test_connection.py

# Test briefing engine
python -c "
from briefing_engine import AgentSDRBriefingEngine
engine = AgentSDRBriefingEngine()
briefing = engine.generate_daily_briefing('test-user', 'test-org')
print('Briefing test:', 'Success' if briefing else 'Failed')
"

# Test follow-up manager
python -c "
from followup_manager import AgentSDRFollowUpManager
manager = AgentSDRFollowUpManager()
queue = manager.get_follow_up_queue('test-user', 'test-org')
print('Follow-up test:', 'Success' if isinstance(queue, list) else 'Failed')
"
```

### 7.3 Integration Testing
```bash
# Test all integrations
python -c "
# Test each module
modules = [
    'briefing_engine',
    'followup_manager', 
    'crm_sync',
    'proposal_generator',
    'opportunity_intelligence',
    'meeting_prep'
]

for module in modules:
    try:
        __import__(module)
        print(f'{module}: ✅ Import successful')
    except Exception as e:
        print(f'{module}: ❌ Import failed - {e}')
"
```

## 👥 Step 8: User Management

### 8.1 Create Sales Team Accounts
```sql
-- Add sales representatives
INSERT INTO users (email, name, role, organization_id, territory, quota_monthly) 
VALUES 
('rep1@company.com', 'Sales Rep 1', 'sales_rep', 'org-id', 'North America', 50000),
('rep2@company.com', 'Sales Rep 2', 'sales_rep', 'org-id', 'Europe', 45000),
('manager@company.com', 'Sales Manager', 'sales_manager', 'org-id', 'Global', 200000);
```

### 8.2 Set Up User Preferences
```sql
-- Configure briefing preferences
UPDATE users SET preferences = '{
    "briefing_time": "08:30",
    "whatsapp_alerts": true,
    "email_summaries": true,
    "ai_insights": true,
    "follow_up_reminders": true
}' WHERE role = 'sales_rep';
```

## 📊 Step 9: Monitoring & Analytics

### 9.1 Application Monitoring
```python
# Add to main.py for basic monitoring
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agentsdr.log'),
        logging.StreamHandler()
    ]
)

@app.before_request
def log_request_info():
    logging.info('Request: %s %s', request.method, request.url)

@app.after_request
def log_response_info(response):
    logging.info('Response: %s', response.status_code)
    return response
```

### 9.2 Performance Metrics
```sql
-- Create performance tracking
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    metric_unit VARCHAR(50),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Example metrics to track
INSERT INTO system_metrics (metric_name, metric_value, metric_unit) VALUES
('daily_briefings_generated', 0, 'count'),
('follow_ups_processed', 0, 'count'),
('proposals_created', 0, 'count'),
('crm_sync_success_rate', 0, 'percentage');
```

## 🔒 Step 10: Security Hardening

### 10.1 Environment Security
```bash
# Ensure secure file permissions
chmod 600 .env.production
chown app:app .env.production

# Use secrets management in production
# Never commit .env.production to git
echo ".env.production" >> .gitignore
```

### 10.2 Database Security
```sql
-- Verify RLS policies are active
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Create additional security policies if needed
CREATE POLICY "admin_all_access" ON users
FOR ALL TO authenticated
USING (auth.jwt() ->> 'role' = 'super_admin');
```

## 📱 Step 11: Mobile Setup

### 11.1 Configure WhatsApp Templates
```bash
# Create WhatsApp message templates
curl -X POST \
  https://graph.facebook.com/v18.0/YOUR_WABA_ID/message_templates \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -d '{
    "name": "daily_briefing",
    "category": "UTILITY",
    "language": "en_US",
    "components": [
      {
        "type": "BODY",
        "text": "Good morning! Your daily sales briefing is ready. You have {{1}} priority leads and {{2}} follow-ups scheduled today."
      }
    ]
  }'
```

## 🎯 Step 12: Go-Live Checklist

### Pre-Launch Verification:
- [ ] All environment variables set
- [ ] Database schema deployed
- [ ] AI integrations working
- [ ] CRM sync functional
- [ ] WhatsApp notifications active
- [ ] User accounts created
- [ ] Permissions configured
- [ ] Backup strategy in place
- [ ] Monitoring active
- [ ] Performance testing passed

### Launch Day:
- [ ] Deploy to production
- [ ] Run health checks
- [ ] Test with sample data
- [ ] Send first briefings
- [ ] Monitor error logs
- [ ] User training session
- [ ] Collect initial feedback

## 🚨 Troubleshooting

### Common Issues:

**Database Connection Failed:**
```bash
# Check Supabase credentials
python test_connection.py
```

**AI Integration Not Working:**
```bash
# Verify OpenAI API key
python -c "import openai; openai.api_key='your-key'; print('API key valid')"
```

**WhatsApp Messages Not Sending:**
```bash
# Check WhatsApp Business API status
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://graph.facebook.com/v18.0/YOUR_PHONE_ID"
```

**CRM Sync Failing:**
```bash
# Test CRM credentials
python -c "from crm_sync import *; # test specific CRM"
```

## 📞 Support & Resources

- **Documentation**: README.md and CLAUDE.md
- **Schema Reference**: agentsdr_schema.sql
- **API Testing**: Use test_*.py scripts
- **Logs**: Check agentsdr.log for errors
- **Database**: Supabase dashboard for data inspection

## 🎉 Success Metrics

Track these KPIs post-deployment:
- Daily briefings generated
- Follow-up completion rate
- Proposal generation volume
- CRM sync success rate
- User engagement metrics
- Sales performance improvements

**Congratulations! Your AgentSDR platform is now production-ready!** 🚀

---

**Need Help?** 
- Review the error logs in `agentsdr.log`
- Check the health endpoint: `/health`
- Verify environment variables are set correctly
- Test individual components with the test scripts