# 🚀 AgentSDR Quick Start Deployment

**Get AgentSDR running in production in under 30 minutes!**

## Step 1: Prerequisites Setup (5 minutes)

### Required Accounts:
1. **Supabase** - [supabase.com](https://supabase.com) (Free tier available)
2. **OpenAI** - [platform.openai.com](https://platform.openai.com) ($5 minimum)
3. **Railway** - [railway.app](https://railway.app) (Free tier available)

### Optional but Recommended:
4. **WhatsApp Business** - For mobile notifications
5. **Your CRM** - Salesforce, HubSpot, Zoho, or Pipedrive

## Step 2: Supabase Database Setup (10 minutes)

### 2.1 Create Supabase Project
```bash
1. Go to supabase.com → "New Project"
2. Choose organization and region
3. Set database password (save this!)
4. Wait for project to be created
```

### 2.2 Deploy Database Schema
```sql
-- In Supabase Dashboard → SQL Editor → "New Query"
-- Copy and paste the entire contents of agentsdr_schema.sql
-- Click "Run" to execute
-- Verify all tables are created (should see ~15 tables)
```

### 2.3 Get Your Supabase Keys
```bash
# In Supabase Dashboard → Settings → API
# Copy these three values:
PROJECT_URL=https://[your-project-id].supabase.co
ANON_KEY=[your-anon-key]
SERVICE_KEY=[your-service-role-key]
```

## Step 3: OpenAI API Setup (5 minutes)

### 3.1 Get OpenAI API Key
```bash
1. Go to platform.openai.com
2. Create account and add $5+ billing
3. Go to API Keys → "Create new secret key"
4. Copy the key: sk-...
```

## Step 4: Quick Local Test (5 minutes)

### 4.1 Clone and Setup
```bash
# Clone the repository
git clone https://github.com/chatgptnotes/agentsdr.git
cd agentsdr
git checkout agentsdr-clean

# Create environment file
cp .env.example .env
```

### 4.2 Configure Environment
Edit your `.env` file:
```bash
# Required - Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Required - Flask
SECRET_KEY=your-super-secret-key-here

# Required - AI
OPENAI_API_KEY=sk-your-openai-key

# Optional - WhatsApp (configure later)
# WHATSAPP_BUSINESS_API_TOKEN=your-token
# WHATSAPP_PHONE_NUMBER_ID=your-phone-id
```

### 4.3 Run Setup Script
```bash
# Install dependencies and test everything
python deploy_setup.py

# If successful, test locally
python main.py
# Open http://localhost:8000
```

## Step 5: Deploy to Railway (5 minutes)

### 5.1 Install Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Or on Mac with Homebrew
brew install railway/tap/railway
```

### 5.2 Deploy to Railway
```bash
# Login to Railway
railway login

# Initialize project
railway init

# Add environment variables
railway variables set SUPABASE_URL="https://your-project-id.supabase.co"
railway variables set SUPABASE_SERVICE_KEY="your-service-key"
railway variables set SUPABASE_ANON_KEY="your-anon-key"
railway variables set SECRET_KEY="your-secret-key"
railway variables set OPENAI_API_KEY="sk-your-openai-key"
railway variables set FLASK_ENV="production"

# Deploy!
railway up
```

### 5.3 Get Your Live URL
```bash
# Railway will provide a URL like:
https://agentsdr-production-xxxx.up.railway.app

# Test your deployment
curl https://your-railway-url.railway.app/health
```

## Step 6: Initial User Setup (3 minutes)

### 6.1 Create Admin User
The setup script automatically creates:
- **Email**: admin@agentsdr.com
- **Password**: Use your Supabase dashboard to set this

### 6.2 Access Your Dashboard
```bash
1. Go to your Railway URL
2. Login with admin@agentsdr.com
3. You should see the AgentSDR dashboard!
```

## Step 7: Test Core Features (5 minutes)

### 7.1 Test Health Check
```bash
# Check system health
curl https://your-url.railway.app/health

# Should return JSON with overall_status: "healthy" or "warning"
```

### 7.2 Test Daily Briefing
```bash
# In your dashboard, you should see:
- Today's briefing section
- Lead metrics
- Activity summary
- AI insights (if OpenAI is working)
```

## 🎉 You're Live!

**Congratulations!** AgentSDR is now running in production!

## Next Steps (Optional):

### Immediate Enhancements:
1. **Add Your Sales Team**: Create user accounts in Supabase
2. **Import Your Leads**: Add leads to the leads table
3. **Configure CRM**: Set up your CRM integration
4. **WhatsApp Setup**: Configure mobile notifications

### Advanced Features:
5. **Custom Branding**: Update colors and logo
6. **Proposal Templates**: Create industry-specific templates
7. **Team Territories**: Set up sales territories
8. **Performance Tracking**: Configure KPI dashboards

## 🚨 Troubleshooting

### Common Issues:

**"Database connection failed"**
```bash
# Check your Supabase URL and keys
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('URL:', os.getenv('SUPABASE_URL'))
print('Key exists:', bool(os.getenv('SUPABASE_SERVICE_KEY')))
"
```

**"AI features not working"**
```bash
# Test OpenAI connection
python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Hello'}],
    max_tokens=5
)
print('OpenAI working!')
"
```

**"Railway deployment failed"**
```bash
# Check Railway logs
railway logs

# Common fix: ensure all environment variables are set
railway variables
```

## 📞 Need Help?

### Quick Commands:
```bash
# Check system health
python health_check.py

# Test database
python health_check.py --component database

# Test AI integration
python health_check.py --component ai

# Full deployment report
python deploy_setup.py
```

### Support Resources:
- **Health Dashboard**: https://your-url/health
- **System Status**: https://your-url/api/system/status
- **Documentation**: PRODUCTION_DEPLOYMENT.md
- **Database**: Your Supabase dashboard

---

**🎯 Your AgentSDR platform is now live and ready to transform your sales process!**

**URL**: `https://your-railway-url.railway.app`
**Admin Login**: `admin@agentsdr.com`
**Health Check**: `https://your-railway-url.railway.app/health`