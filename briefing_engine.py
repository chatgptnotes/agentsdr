"""
AgentSDR Daily Briefing Engine
Generates personalized daily briefings for sales representatives
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import openai
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Lead:
    id: str
    name: str
    company: str
    status: str
    lead_score: int
    last_contacted: Optional[datetime]
    next_follow_up: Optional[datetime]
    assigned_to: str
    notes: str

@dataclass
class Opportunity:
    id: str
    name: str
    stage: str
    value: float
    probability: int
    expected_close_date: Optional[datetime]
    lead_name: str
    company: str
    assigned_to: str

@dataclass
class Activity:
    id: str
    type: str
    subject: str
    status: str
    priority: str
    due_date: Optional[datetime]
    lead_name: str
    company: str
    assigned_to: str

@dataclass
class BriefingContent:
    date: datetime
    user_id: str
    priority_leads: List[Dict]
    follow_up_tasks: List[Dict]
    opportunities_update: List[Dict]
    new_leads: List[Dict]
    at_risk_opportunities: List[Dict]
    performance_metrics: Dict
    ai_insights: List[Dict]
    recommendations: List[str]

class AgentSDRBriefingEngine:
    """
    Core engine for generating personalized daily briefings for sales representatives
    """
    
    def __init__(self):
        self.openai_client = None
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.whatsapp_token = os.getenv('WHATSAPP_BUSINESS_API_TOKEN')
        
        # Initialize OpenAI if API key is available
        if os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_client = openai
    
    def generate_daily_briefing(self, user_id: str, organization_id: str) -> BriefingContent:
        """
        Generate a comprehensive daily briefing for a sales representative
        """
        try:
            # Get user preferences
            user_preferences = self._get_user_preferences(user_id)
            
            # Collect data for briefing
            priority_leads = self._get_priority_leads(user_id, organization_id)
            follow_up_tasks = self._get_follow_up_tasks(user_id, organization_id)
            opportunities = self._get_opportunities_update(user_id, organization_id)
            new_leads = self._get_new_leads(user_id, organization_id)
            at_risk_opportunities = self._identify_at_risk_opportunities(user_id, organization_id)
            performance_metrics = self._calculate_performance_metrics(user_id, organization_id)
            
            # Generate AI insights if available
            ai_insights = []
            recommendations = []
            
            if self.openai_client:
                ai_insights = self._generate_ai_insights(
                    priority_leads, opportunities, at_risk_opportunities
                )
                recommendations = self._generate_recommendations(
                    user_id, performance_metrics, priority_leads
                )
            
            # Create briefing content
            briefing = BriefingContent(
                date=datetime.now(timezone.utc),
                user_id=user_id,
                priority_leads=priority_leads,
                follow_up_tasks=follow_up_tasks,
                opportunities_update=opportunities,
                new_leads=new_leads,
                at_risk_opportunities=at_risk_opportunities,
                performance_metrics=performance_metrics,
                ai_insights=ai_insights,
                recommendations=recommendations
            )
            
            # Save briefing to database
            self._save_briefing(briefing, organization_id)
            
            return briefing
            
        except Exception as e:
            print(f"Error generating briefing: {e}")
            return self._generate_fallback_briefing(user_id, organization_id)
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user's briefing preferences"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/users?id=eq.{user_id}&select=preferences",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data[0].get('preferences', {}) if data else {}
            
            return {}
        except Exception as e:
            print(f"Error getting user preferences: {e}")
            return {}
    
    def _get_priority_leads(self, user_id: str, organization_id: str) -> List[Dict]:
        """Get priority leads requiring immediate attention"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Get leads with high scores or overdue follow-ups
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/leads",
                headers=headers,
                params={
                    'assigned_to': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'or': f'(lead_score.gte.70,next_follow_up.lt.{yesterday})',
                    'status': 'neq.converted',
                    'order': 'lead_score.desc,next_follow_up.asc',
                    'limit': 10
                }
            )
            
            if response.status_code == 200:
                leads = response.json()
                return [
                    {
                        'id': lead['id'],
                        'name': f"{lead['first_name']} {lead['last_name']}",
                        'company': lead['company'],
                        'lead_score': lead['lead_score'],
                        'status': lead['status'],
                        'last_contacted': lead['last_contacted'],
                        'next_follow_up': lead['next_follow_up'],
                        'priority_reason': self._determine_priority_reason(lead)
                    }
                    for lead in leads
                ]
            
            return []
        except Exception as e:
            print(f"Error getting priority leads: {e}")
            return []
    
    def _get_follow_up_tasks(self, user_id: str, organization_id: str) -> List[Dict]:
        """Get overdue and upcoming follow-up tasks"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            today = datetime.now().date().isoformat()
            tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/activities",
                headers=headers,
                params={
                    'assigned_to': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'status': 'eq.planned',
                    'due_date': f'lte.{tomorrow}',
                    'order': 'due_date.asc,priority.desc',
                    'limit': 15
                }
            )
            
            if response.status_code == 200:
                activities = response.json()
                return [
                    {
                        'id': activity['id'],
                        'type': activity['type'],
                        'subject': activity['subject'],
                        'due_date': activity['due_date'],
                        'priority': activity['priority'],
                        'is_overdue': activity['due_date'] < today if activity['due_date'] else False,
                        'lead_info': self._get_lead_info_for_activity(activity['lead_id'])
                    }
                    for activity in activities
                ]
            
            return []
        except Exception as e:
            print(f"Error getting follow-up tasks: {e}")
            return []
    
    def _get_opportunities_update(self, user_id: str, organization_id: str) -> List[Dict]:
        """Get opportunities requiring attention"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/opportunities",
                headers=headers,
                params={
                    'assigned_to': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'stage': 'neq.closed_won,neq.closed_lost',
                    'order': 'expected_close_date.asc,value.desc',
                    'limit': 10
                }
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                return [
                    {
                        'id': opp['id'],
                        'name': opp['name'],
                        'stage': opp['stage'],
                        'value': opp['value'],
                        'probability': opp['probability'],
                        'expected_close_date': opp['expected_close_date'],
                        'days_to_close': self._calculate_days_to_close(opp['expected_close_date']),
                        'status_update': self._generate_opportunity_status(opp)
                    }
                    for opp in opportunities
                ]
            
            return []
        except Exception as e:
            print(f"Error getting opportunities: {e}")
            return []
    
    def _get_new_leads(self, user_id: str, organization_id: str) -> List[Dict]:
        """Get new leads from the last 24 hours"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/leads",
                headers=headers,
                params={
                    'assigned_to': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'created_at': f'gte.{yesterday}',
                    'order': 'created_at.desc',
                    'limit': 5
                }
            )
            
            if response.status_code == 200:
                leads = response.json()
                return [
                    {
                        'id': lead['id'],
                        'name': f"{lead['first_name']} {lead['last_name']}",
                        'company': lead['company'],
                        'lead_source': lead['lead_source'],
                        'lead_score': lead['lead_score'],
                        'created_at': lead['created_at']
                    }
                    for lead in leads
                ]
            
            return []
        except Exception as e:
            print(f"Error getting new leads: {e}")
            return []
    
    def _identify_at_risk_opportunities(self, user_id: str, organization_id: str) -> List[Dict]:
        """Identify opportunities that might be at risk"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Get opportunities with no recent activity
            two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/opportunities",
                headers=headers,
                params={
                    'assigned_to': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'stage': 'neq.closed_won,neq.closed_lost',
                    'updated_at': f'lt.{two_weeks_ago}',
                    'order': 'value.desc',
                    'limit': 5
                }
            )
            
            if response.status_code == 200:
                opportunities = response.json()
                at_risk = []
                
                for opp in opportunities:
                    risk_factors = self._assess_risk_factors(opp)
                    if risk_factors:
                        at_risk.append({
                            'id': opp['id'],
                            'name': opp['name'],
                            'value': opp['value'],
                            'stage': opp['stage'],
                            'risk_factors': risk_factors,
                            'last_activity': opp['updated_at']
                        })
                
                return at_risk
            
            return []
        except Exception as e:
            print(f"Error identifying at-risk opportunities: {e}")
            return []
    
    def _calculate_performance_metrics(self, user_id: str, organization_id: str) -> Dict:
        """Calculate performance metrics for the user"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Get metrics for current week and previous week
            current_week_start = (datetime.now() - timedelta(days=7)).isoformat()
            
            # Get current week metrics
            response = requests.get(
                f"{self.supabase_url}/rest/v1/performance_metrics",
                headers=headers,
                params={
                    'user_id': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'metric_date': f'gte.{current_week_start}',
                    'order': 'metric_date.desc',
                    'limit': 7
                }
            )
            
            if response.status_code == 200:
                metrics = response.json()
                
                if metrics:
                    # Aggregate weekly metrics
                    total_leads = sum(m['leads_created'] for m in metrics)
                    total_activities = sum(m['activities_completed'] for m in metrics)
                    total_calls = sum(m['calls_made'] for m in metrics)
                    total_emails = sum(m['emails_sent'] for m in metrics)
                    total_revenue = sum(m['revenue_generated'] for m in metrics)
                    
                    return {
                        'leads_created_week': total_leads,
                        'activities_completed_week': total_activities,
                        'calls_made_week': total_calls,
                        'emails_sent_week': total_emails,
                        'revenue_generated_week': total_revenue,
                        'quota_achievement': metrics[0]['quota_achievement'] if metrics else 0
                    }
            
            return {
                'leads_created_week': 0,
                'activities_completed_week': 0,
                'calls_made_week': 0,
                'emails_sent_week': 0,
                'revenue_generated_week': 0,
                'quota_achievement': 0
            }
            
        except Exception as e:
            print(f"Error calculating performance metrics: {e}")
            return {}
    
    def _generate_ai_insights(self, priority_leads: List[Dict], 
                            opportunities: List[Dict], 
                            at_risk_opportunities: List[Dict]) -> List[Dict]:
        """Generate AI-powered insights using OpenAI"""
        if not self.openai_client:
            return []
        
        try:
            # Prepare context for AI
            context = {
                'priority_leads_count': len(priority_leads),
                'opportunities_count': len(opportunities),
                'at_risk_count': len(at_risk_opportunities),
                'priority_leads': priority_leads[:3],  # Top 3 for context
                'at_risk_opportunities': at_risk_opportunities
            }
            
            prompt = f"""
            As an AI sales assistant, analyze the following sales data and provide 2-3 key insights:
            
            Priority Leads: {context['priority_leads_count']}
            Active Opportunities: {context['opportunities_count']}
            At-Risk Opportunities: {context['at_risk_count']}
            
            Focus on actionable insights about lead prioritization, opportunity risks, and sales strategy.
            Keep insights concise and specific.
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert sales AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            insights_text = response.choices[0].message.content.strip()
            insights = insights_text.split('\n')
            
            return [
                {
                    'type': 'ai_insight',
                    'title': f'Insight {i+1}',
                    'description': insight.strip(),
                    'confidence': 0.85
                }
                for i, insight in enumerate(insights[:3]) if insight.strip()
            ]
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return []
    
    def _generate_recommendations(self, user_id: str, performance_metrics: Dict, 
                                priority_leads: List[Dict]) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        if performance_metrics.get('calls_made_week', 0) < 20:
            recommendations.append("Consider increasing call volume - aim for 4-5 calls per day")
        
        if performance_metrics.get('quota_achievement', 0) < 80:
            recommendations.append("Focus on high-value opportunities to improve quota achievement")
        
        # Lead-based recommendations
        high_score_leads = [l for l in priority_leads if l.get('lead_score', 0) > 80]
        if high_score_leads:
            recommendations.append(f"Prioritize {len(high_score_leads)} high-score leads for immediate follow-up")
        
        overdue_followups = [l for l in priority_leads if l.get('priority_reason') == 'overdue_followup']
        if overdue_followups:
            recommendations.append(f"Address {len(overdue_followups)} overdue follow-ups today")
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def _save_briefing(self, briefing: BriefingContent, organization_id: str):
        """Save briefing to database"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            briefing_data = {
                'user_id': briefing.user_id,
                'organization_id': organization_id,
                'briefing_date': briefing.date.date().isoformat(),
                'content': {
                    'priority_leads': briefing.priority_leads,
                    'follow_up_tasks': briefing.follow_up_tasks,
                    'opportunities_update': briefing.opportunities_update,
                    'new_leads': briefing.new_leads,
                    'at_risk_opportunities': briefing.at_risk_opportunities,
                    'performance_metrics': briefing.performance_metrics,
                    'ai_insights': briefing.ai_insights,
                    'recommendations': briefing.recommendations
                }
            }
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/daily_briefings",
                headers=headers,
                json=briefing_data
            )
            
            if response.status_code == 201:
                print("Briefing saved successfully")
            else:
                print(f"Error saving briefing: {response.text}")
                
        except Exception as e:
            print(f"Error saving briefing: {e}")
    
    def send_whatsapp_briefing(self, user_phone: str, briefing: BriefingContent) -> bool:
        """Send briefing summary via WhatsApp"""
        if not self.whatsapp_token:
            print("WhatsApp token not configured")
            return False
        
        try:
            # Format briefing for WhatsApp
            message = self._format_whatsapp_message(briefing)
            
            # Send via WhatsApp Business API
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': user_phone,
                'type': 'text',
                'text': {'body': message}
            }
            
            response = requests.post(
                f"https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages",
                headers=headers,
                json=payload
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending WhatsApp briefing: {e}")
            return False
    
    def _format_whatsapp_message(self, briefing: BriefingContent) -> str:
        """Format briefing content for WhatsApp"""
        message = f"🌅 *Good Morning! Your Daily Sales Briefing*\n\n"
        
        # Priority items
        if briefing.priority_leads:
            message += f"🎯 *Priority Leads ({len(briefing.priority_leads)})*\n"
            for lead in briefing.priority_leads[:3]:
                message += f"• {lead['name']} ({lead['company']}) - Score: {lead['lead_score']}\n"
            message += "\n"
        
        # Follow-ups
        if briefing.follow_up_tasks:
            overdue = [t for t in briefing.follow_up_tasks if t.get('is_overdue')]
            if overdue:
                message += f"⚠️ *Overdue Follow-ups ({len(overdue)})*\n"
                for task in overdue[:2]:
                    message += f"• {task['subject']}\n"
                message += "\n"
        
        # At-risk opportunities
        if briefing.at_risk_opportunities:
            message += f"🚨 *At-Risk Opportunities ({len(briefing.at_risk_opportunities)})*\n"
            for opp in briefing.at_risk_opportunities[:2]:
                message += f"• {opp['name']} - ${opp['value']:,.0f}\n"
            message += "\n"
        
        # Performance
        metrics = briefing.performance_metrics
        if metrics:
            message += f"📊 *This Week's Performance*\n"
            message += f"• Leads: {metrics.get('leads_created_week', 0)}\n"
            message += f"• Calls: {metrics.get('calls_made_week', 0)}\n"
            message += f"• Quota: {metrics.get('quota_achievement', 0):.0f}%\n\n"
        
        # AI recommendations
        if briefing.recommendations:
            message += f"💡 *Today's Focus*\n"
            for rec in briefing.recommendations[:2]:
                message += f"• {rec}\n"
        
        message += "\n🚀 *Have a productive day!*"
        return message
    
    def _determine_priority_reason(self, lead: Dict) -> str:
        """Determine why a lead is priority"""
        if lead.get('lead_score', 0) >= 80:
            return 'high_score'
        elif lead.get('next_follow_up') and lead['next_follow_up'] < datetime.now().isoformat():
            return 'overdue_followup'
        else:
            return 'general_priority'
    
    def _get_lead_info_for_activity(self, lead_id: str) -> Dict:
        """Get lead information for an activity"""
        if not lead_id:
            return {}
        
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/leads?id=eq.{lead_id}&select=first_name,last_name,company",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    lead = data[0]
                    return {
                        'name': f"{lead['first_name']} {lead['last_name']}",
                        'company': lead['company']
                    }
            
            return {}
        except Exception as e:
            print(f"Error getting lead info: {e}")
            return {}
    
    def _calculate_days_to_close(self, expected_close_date: str) -> int:
        """Calculate days until expected close date"""
        if not expected_close_date:
            return 999
        
        try:
            close_date = datetime.fromisoformat(expected_close_date.replace('Z', '+00:00'))
            today = datetime.now(timezone.utc)
            return (close_date - today).days
        except:
            return 999
    
    def _generate_opportunity_status(self, opportunity: Dict) -> str:
        """Generate status update for opportunity"""
        days_to_close = self._calculate_days_to_close(opportunity.get('expected_close_date'))
        
        if days_to_close < 7:
            return f"Closing in {days_to_close} days - needs immediate attention"
        elif days_to_close < 30:
            return f"Closing in {days_to_close} days - on track"
        else:
            return "Long-term opportunity - maintain regular contact"
    
    def _assess_risk_factors(self, opportunity: Dict) -> List[str]:
        """Assess risk factors for an opportunity"""
        risk_factors = []
        
        # Check for inactivity
        if opportunity.get('updated_at'):
            try:
                last_update = datetime.fromisoformat(opportunity['updated_at'].replace('Z', '+00:00'))
                days_inactive = (datetime.now(timezone.utc) - last_update).days
                
                if days_inactive > 14:
                    risk_factors.append(f"No activity for {days_inactive} days")
            except:
                pass
        
        # Check close date
        days_to_close = self._calculate_days_to_close(opportunity.get('expected_close_date'))
        if days_to_close < 0:
            risk_factors.append("Past expected close date")
        
        # Check probability vs stage
        stage = opportunity.get('stage', '').lower()
        probability = opportunity.get('probability', 0)
        
        if stage in ['proposal', 'negotiation'] and probability < 60:
            risk_factors.append("Low probability for advanced stage")
        
        return risk_factors
    
    def _generate_fallback_briefing(self, user_id: str, organization_id: str) -> BriefingContent:
        """Generate a fallback briefing when main generation fails"""
        return BriefingContent(
            date=datetime.now(timezone.utc),
            user_id=user_id,
            priority_leads=[],
            follow_up_tasks=[],
            opportunities_update=[],
            new_leads=[],
            at_risk_opportunities=[],
            performance_metrics={},
            ai_insights=[],
            recommendations=["Check your CRM for today's priorities", "Follow up on recent leads"]
        )

# Example usage and testing
if __name__ == "__main__":
    engine = AgentSDRBriefingEngine()
    
    # Test briefing generation
    test_user_id = "test-user-123"
    test_org_id = "test-org-456"
    
    print("Generating daily briefing...")
    briefing = engine.generate_daily_briefing(test_user_id, test_org_id)
    
    print(f"Briefing generated for {briefing.date}")
    print(f"Priority leads: {len(briefing.priority_leads)}")
    print(f"Follow-up tasks: {len(briefing.follow_up_tasks)}")
    print(f"Opportunities: {len(briefing.opportunities_update)}")
    print(f"AI insights: {len(briefing.ai_insights)}")
    print(f"Recommendations: {len(briefing.recommendations)}")