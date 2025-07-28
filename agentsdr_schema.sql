-- AgentSDR Database Schema
-- Sales Development Representative Assistant Platform
-- Run this in your Supabase SQL editor to set up the sales-focused database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- CORE SALES ORGANIZATION TABLES
-- ========================================

-- Organizations table (Sales Teams/Companies)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    industry VARCHAR(100),
    website VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'trial')),
    plan_type VARCHAR(50) DEFAULT 'trial' CHECK (plan_type IN ('trial', 'starter', 'professional', 'enterprise')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (Sales Representatives and Managers)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'sales_rep' CHECK (role IN ('super_admin', 'sales_manager', 'sales_rep', 'admin')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    territory VARCHAR(255), -- Sales territory assignment
    quota_monthly DECIMAL(12,2), -- Monthly sales quota
    phone VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}', -- User preferences for briefings, notifications
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- LEAD AND PROSPECT MANAGEMENT
-- ========================================

-- Leads table (Prospects and potential customers)
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    company VARCHAR(255),
    job_title VARCHAR(255),
    industry VARCHAR(100),
    lead_source VARCHAR(100), -- 'website', 'referral', 'cold_outreach', 'linkedin', etc.
    lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),
    status VARCHAR(50) DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'unqualified', 'converted', 'lost')),
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    notes TEXT,
    tags VARCHAR(500), -- Comma-separated tags
    location JSONB, -- City, state, country info
    social_profiles JSONB, -- LinkedIn, Twitter, etc.
    last_contacted TIMESTAMP WITH TIME ZONE,
    next_follow_up TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Opportunities table (Active sales pipeline)
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    stage VARCHAR(50) DEFAULT 'prospecting' CHECK (stage IN (
        'prospecting', 'qualification', 'needs_analysis', 'proposal', 
        'negotiation', 'closed_won', 'closed_lost'
    )),
    value DECIMAL(12,2), -- Opportunity value
    probability INTEGER DEFAULT 10 CHECK (probability >= 0 AND probability <= 100),
    expected_close_date DATE,
    actual_close_date DATE,
    loss_reason VARCHAR(255), -- If closed_lost
    competitor VARCHAR(255), -- Primary competitor
    description TEXT,
    requirements JSONB, -- Customer requirements and needs
    decision_makers JSONB, -- Array of decision maker info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- ACTIVITY AND COMMUNICATION TRACKING
-- ========================================

-- Activities table (Follow-ups, calls, emails, meetings)
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'call', 'email', 'meeting', 'task', 'note', 'follow_up', 'demo', 'proposal_sent'
    )),
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planned' CHECK (status IN ('planned', 'completed', 'cancelled', 'overdue')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_date TIMESTAMP WITH TIME ZONE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    duration_minutes INTEGER, -- For calls and meetings
    outcome VARCHAR(100), -- Call/meeting outcome
    next_action TEXT, -- Recommended next action
    attachments JSONB, -- File attachments info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- PROPOSAL AND CONTENT MANAGEMENT
-- ========================================

-- Proposal templates
CREATE TABLE IF NOT EXISTS proposal_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    industry VARCHAR(100),
    template_type VARCHAR(50) CHECK (template_type IN ('standard', 'custom', 'industry_specific')),
    content JSONB NOT NULL, -- Template structure and content
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated proposals
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    template_id UUID REFERENCES proposal_templates(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'viewed', 'accepted', 'rejected')),
    content JSONB NOT NULL, -- Proposal content
    total_value DECIMAL(12,2),
    sent_date TIMESTAMP WITH TIME ZONE,
    viewed_date TIMESTAMP WITH TIME ZONE,
    response_date TIMESTAMP WITH TIME ZONE,
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- DAILY BRIEFING AND INTELLIGENCE
-- ========================================

-- Daily briefings
CREATE TABLE IF NOT EXISTS daily_briefings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    briefing_date DATE NOT NULL,
    content JSONB NOT NULL, -- Briefing content structure
    priority_leads JSONB, -- Priority leads for the day
    follow_up_tasks JSONB, -- Follow-up tasks
    opportunities_update JSONB, -- Pipeline updates
    metrics JSONB, -- Performance metrics
    sent_at TIMESTAMP WITH TIME ZONE,
    viewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Intelligence insights (AI-generated insights)
CREATE TABLE IF NOT EXISTS intelligence_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'lead_score_change', 'opportunity_risk', 'competitor_mention', 
        'buying_signal', 'engagement_pattern', 'follow_up_reminder'
    )),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT false,
    is_actionable BOOLEAN DEFAULT true,
    action_taken BOOLEAN DEFAULT false,
    metadata JSONB, -- Additional insight data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- CRM INTEGRATION AND SYNC
-- ========================================

-- CRM integrations
CREATE TABLE IF NOT EXISTS crm_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    crm_type VARCHAR(50) NOT NULL CHECK (crm_type IN ('salesforce', 'hubspot', 'zoho', 'pipedrive', 'custom')),
    integration_name VARCHAR(255) NOT NULL,
    credentials JSONB, -- Encrypted CRM credentials
    mapping_config JSONB, -- Field mapping configuration
    sync_settings JSONB, -- Sync frequency and rules
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    last_sync TIMESTAMP WITH TIME ZONE,
    next_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CRM sync logs
CREATE TABLE IF NOT EXISTS crm_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES crm_integrations(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) CHECK (sync_type IN ('full', 'incremental', 'manual')),
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_details JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- ========================================
-- COMMUNICATION CHANNELS
-- ========================================

-- WhatsApp message logs
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_type VARCHAR(50) CHECK (message_type IN ('briefing', 'alert', 'reminder', 'notification')),
    recipient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    message_content TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
    whatsapp_message_id VARCHAR(255), -- WhatsApp API message ID
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email templates and logs
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) CHECK (template_type IN ('follow_up', 'introduction', 'proposal', 'meeting_request', 'thank_you')),
    content TEXT NOT NULL, -- HTML content
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- PERFORMANCE ANALYTICS
-- ========================================

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    leads_created INTEGER DEFAULT 0,
    leads_contacted INTEGER DEFAULT 0,
    opportunities_created INTEGER DEFAULT 0,
    opportunities_won INTEGER DEFAULT 0,
    activities_completed INTEGER DEFAULT 0,
    calls_made INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    meetings_held INTEGER DEFAULT 0,
    revenue_generated DECIMAL(12,2) DEFAULT 0,
    quota_achievement DECIMAL(5,2) DEFAULT 0, -- Percentage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Core table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Lead management indexes
CREATE INDEX IF NOT EXISTS idx_leads_organization_id ON leads(organization_id);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to ON leads(assigned_to);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_lead_score ON leads(lead_score);
CREATE INDEX IF NOT EXISTS idx_leads_next_follow_up ON leads(next_follow_up);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company);

-- Opportunity indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_organization_id ON opportunities(organization_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_assigned_to ON opportunities(assigned_to);
CREATE INDEX IF NOT EXISTS idx_opportunities_stage ON opportunities(stage);
CREATE INDEX IF NOT EXISTS idx_opportunities_expected_close_date ON opportunities(expected_close_date);

-- Activity indexes
CREATE INDEX IF NOT EXISTS idx_activities_organization_id ON activities(organization_id);
CREATE INDEX IF NOT EXISTS idx_activities_assigned_to ON activities(assigned_to);
CREATE INDEX IF NOT EXISTS idx_activities_lead_id ON activities(lead_id);
CREATE INDEX IF NOT EXISTS idx_activities_due_date ON activities(due_date);
CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status);
CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(type);

-- Intelligence and briefing indexes
CREATE INDEX IF NOT EXISTS idx_daily_briefings_user_id ON daily_briefings(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_briefings_date ON daily_briefings(briefing_date);
CREATE INDEX IF NOT EXISTS idx_intelligence_insights_user_id ON intelligence_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_intelligence_insights_type ON intelligence_insights(type);
CREATE INDEX IF NOT EXISTS idx_intelligence_insights_created_at ON intelligence_insights(created_at);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_performance_metrics_user_id ON performance_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(metric_date);

-- ========================================
-- ROW LEVEL SECURITY (RLS)
-- ========================================

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposal_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_briefings ENABLE ROW LEVEL SECURITY;
ALTER TABLE intelligence_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;

-- ========================================
-- RLS POLICIES
-- ========================================

-- Organizations: Super admins can see all, others only their own
CREATE POLICY "Organizations access policy" ON organizations
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'super_admin' OR 
        id IN (
            SELECT organization_id FROM users 
            WHERE id = (auth.jwt() ->> 'user_id')::uuid
        )
    );

-- Users: Users can see users in their organization
CREATE POLICY "Users access policy" ON users
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'super_admin' OR 
        organization_id IN (
            SELECT organization_id FROM users 
            WHERE id = (auth.jwt() ->> 'user_id')::uuid
        )
    );

-- Leads: Users can see leads in their organization
CREATE POLICY "Leads access policy" ON leads
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id FROM users 
            WHERE id = (auth.jwt() ->> 'user_id')::uuid
        )
    );

-- Opportunities: Users can see opportunities in their organization
CREATE POLICY "Opportunities access policy" ON opportunities
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id FROM users 
            WHERE id = (auth.jwt() ->> 'user_id')::uuid
        )
    );

-- Activities: Users can see activities in their organization
CREATE POLICY "Activities access policy" ON activities
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id FROM users 
            WHERE id = (auth.jwt() ->> 'user_id')::uuid
        )
    );

-- Daily briefings: Users can only see their own briefings
CREATE POLICY "Daily briefings access policy" ON daily_briefings
    FOR ALL USING (
        user_id = (auth.jwt() ->> 'user_id')::uuid OR
        auth.jwt() ->> 'role' IN ('super_admin', 'sales_manager')
    );

-- Intelligence insights: Users can see insights in their organization
CREATE POLICY "Intelligence insights access policy" ON intelligence_insights
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id FROM users 
            WHERE id = (auth.jwt() ->> 'user_id')::uuid
        )
    );

-- Performance metrics: Users can see metrics in their organization
CREATE POLICY "Performance metrics access policy" ON performance_metrics
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id FROM users 
            WHERE id = (auth.jwt() ->> 'user_id')::uuid
        )
    );

-- ========================================
-- INITIAL DATA SETUP
-- ========================================

-- Insert default organization for testing
INSERT INTO organizations (name, description, status, plan_type) 
VALUES ('AgentSDR Demo Organization', 'Demo organization for AgentSDR testing', 'active', 'trial')
ON CONFLICT DO NOTHING;

-- Insert super admin user
INSERT INTO users (email, name, role, organization_id, status) 
VALUES (
    'admin@agentsdr.com', 
    'AgentSDR Admin', 
    'super_admin', 
    (SELECT id FROM organizations WHERE name = 'AgentSDR Demo Organization'),
    'active'
) ON CONFLICT (email) DO NOTHING;

-- ========================================
-- FUNCTIONS AND TRIGGERS
-- ========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_opportunities_updated_at BEFORE UPDATE ON opportunities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_activities_updated_at BEFORE UPDATE ON activities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_crm_integrations_updated_at BEFORE UPDATE ON crm_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate lead score based on activities and engagement
CREATE OR REPLACE FUNCTION calculate_lead_score(lead_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    score INTEGER := 0;
    activity_count INTEGER;
    email_opens INTEGER;
    last_activity_days INTEGER;
BEGIN
    -- Base score from lead source
    SELECT CASE 
        WHEN lead_source = 'referral' THEN 30
        WHEN lead_source = 'website' THEN 20
        WHEN lead_source = 'linkedin' THEN 15
        ELSE 10
    END INTO score
    FROM leads WHERE id = lead_uuid;
    
    -- Add points for activities
    SELECT COUNT(*) INTO activity_count
    FROM activities 
    WHERE lead_id = lead_uuid AND status = 'completed';
    
    score := score + (activity_count * 5);
    
    -- Deduct points for inactivity
    SELECT EXTRACT(days FROM NOW() - MAX(created_at)) INTO last_activity_days
    FROM activities 
    WHERE lead_id = lead_uuid;
    
    IF last_activity_days > 30 THEN
        score := score - 10;
    END IF;
    
    -- Ensure score is within bounds
    score := GREATEST(0, LEAST(100, score));
    
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE organizations IS 'Sales organizations/companies using AgentSDR';
COMMENT ON TABLE users IS 'Sales representatives and managers';
COMMENT ON TABLE leads IS 'Prospects and potential customers';
COMMENT ON TABLE opportunities IS 'Active sales pipeline opportunities';
COMMENT ON TABLE activities IS 'Sales activities: calls, emails, meetings, tasks';
COMMENT ON TABLE daily_briefings IS 'AI-generated daily briefings for sales reps';
COMMENT ON TABLE intelligence_insights IS 'AI-powered sales insights and recommendations';
COMMENT ON TABLE crm_integrations IS 'CRM system integration configurations';
COMMENT ON TABLE performance_metrics IS 'Sales performance tracking and analytics';

-- Schema version for migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO schema_version (version) VALUES ('1.0.0-agentsdr') ON CONFLICT DO NOTHING;