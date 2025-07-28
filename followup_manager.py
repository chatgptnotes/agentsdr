"""
AgentSDR Follow-Up Management System
Automated prospect tracking and engagement management for sales representatives
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from dotenv import load_dotenv

load_dotenv()

class FollowUpType(Enum):
    INITIAL_CONTACT = "initial_contact"
    FOLLOW_UP_CALL = "follow_up_call"
    EMAIL_FOLLOW_UP = "email_follow_up"
    DEMO_FOLLOW_UP = "demo_follow_up"
    PROPOSAL_FOLLOW_UP = "proposal_follow_up"
    DECISION_FOLLOW_UP = "decision_follow_up"
    NURTURE_SEQUENCE = "nurture_sequence"

class FollowUpPriority(Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class LeadEngagementLevel(Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    RESPONSIVE = "responsive"
    UNRESPONSIVE = "unresponsive"

@dataclass
class FollowUpTask:
    id: str
    lead_id: str
    lead_name: str
    company: str
    task_type: FollowUpType
    priority: FollowUpPriority
    due_date: datetime
    status: str
    description: str
    contact_history: List[Dict]
    engagement_level: LeadEngagementLevel
    recommended_action: str
    context: Dict

@dataclass
class FollowUpSequence:
    sequence_id: str
    name: str
    lead_id: str
    sequence_type: str
    current_step: int
    total_steps: int
    is_active: bool
    next_action_date: datetime
    template_data: Dict

class AgentSDRFollowUpManager:
    """
    Intelligent follow-up management system that tracks prospect engagement,
    automates follow-up scheduling, and provides personalized recommendations
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.openai_client = None
        
        if os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_client = openai
    
    def get_follow_up_queue(self, user_id: str, organization_id: str, 
                           days_ahead: int = 7) -> List[FollowUpTask]:
        """
        Get prioritized follow-up queue for a sales representative
        """
        try:
            # Get overdue and upcoming follow-ups
            overdue_tasks = self._get_overdue_followups(user_id, organization_id)
            upcoming_tasks = self._get_upcoming_followups(user_id, organization_id, days_ahead)
            
            # Combine and prioritize
            all_tasks = overdue_tasks + upcoming_tasks
            
            # Add AI-powered prioritization
            if self.openai_client and all_tasks:
                all_tasks = self._ai_prioritize_tasks(all_tasks)
            
            # Sort by priority and due date
            all_tasks.sort(key=lambda x: (
                0 if x.priority == FollowUpPriority.URGENT else
                1 if x.priority == FollowUpPriority.HIGH else
                2 if x.priority == FollowUpPriority.MEDIUM else 3,
                x.due_date
            ))
            
            return all_tasks[:50]  # Limit to top 50 tasks
            
        except Exception as e:
            print(f"Error getting follow-up queue: {e}")
            return []
    
    def _get_overdue_followups(self, user_id: str, organization_id: str) -> List[FollowUpTask]:
        """Get overdue follow-up tasks"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            today = datetime.now().isoformat()
            
            # Get overdue activities
            response = requests.get(
                f"{self.supabase_url}/rest/v1/activities",
                headers=headers,
                params={
                    'assigned_to': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'status': 'eq.planned',
                    'due_date': f'lt.{today}',
                    'type': 'in.(follow_up,call,email)',
                    'order': 'due_date.asc',
                    'limit': 25
                }
            )
            
            if response.status_code == 200:
                activities = response.json()
                tasks = []
                
                for activity in activities:
                    # Get lead information
                    lead_info = self._get_lead_details(activity['lead_id'])
                    if not lead_info:
                        continue
                    
                    # Get contact history
                    contact_history = self._get_contact_history(activity['lead_id'])
                    
                    # Determine engagement level
                    engagement_level = self._assess_engagement_level(contact_history)
                    
                    task = FollowUpTask(
                        id=activity['id'],
                        lead_id=activity['lead_id'],
                        lead_name=lead_info.get('name', 'Unknown'),
                        company=lead_info.get('company', 'Unknown'),
                        task_type=self._map_activity_type(activity['type']),
                        priority=FollowUpPriority.URGENT,  # Overdue = urgent
                        due_date=datetime.fromisoformat(activity['due_date'].replace('Z', '+00:00')),
                        status='overdue',
                        description=activity['description'] or activity['subject'],
                        contact_history=contact_history,
                        engagement_level=engagement_level,
                        recommended_action=self._generate_recommended_action(
                            activity, lead_info, contact_history, engagement_level
                        ),
                        context={
                            'days_overdue': (datetime.now(timezone.utc) - 
                                           datetime.fromisoformat(activity['due_date'].replace('Z', '+00:00'))).days,
                            'lead_score': lead_info.get('lead_score', 0),
                            'last_contact_days': self._days_since_last_contact(contact_history)
                        }
                    )
                    tasks.append(task)
                
                return tasks
            
            return []
            
        except Exception as e:
            print(f"Error getting overdue follow-ups: {e}")
            return []
    
    def _get_upcoming_followups(self, user_id: str, organization_id: str, 
                               days_ahead: int) -> List[FollowUpTask]:
        """Get upcoming follow-up tasks"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            today = datetime.now().isoformat()
            future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
            
            # Get upcoming activities
            response = requests.get(
                f"{self.supabase_url}/rest/v1/activities",
                headers=headers,
                params={
                    'assigned_to': f'eq.{user_id}',
                    'organization_id': f'eq.{organization_id}',
                    'status': 'eq.planned',
                    'due_date': f'gte.{today}&due_date=lte.{future_date}',
                    'type': 'in.(follow_up,call,email)',
                    'order': 'due_date.asc,priority.desc',
                    'limit': 30
                }
            )
            
            if response.status_code == 200:
                activities = response.json()
                tasks = []
                
                for activity in activities:
                    lead_info = self._get_lead_details(activity['lead_id'])
                    if not lead_info:
                        continue
                    
                    contact_history = self._get_contact_history(activity['lead_id'])
                    engagement_level = self._assess_engagement_level(contact_history)
                    
                    # Determine priority based on various factors
                    priority = self._calculate_task_priority(
                        activity, lead_info, contact_history, engagement_level
                    )
                    
                    task = FollowUpTask(
                        id=activity['id'],
                        lead_id=activity['lead_id'],
                        lead_name=lead_info.get('name', 'Unknown'),
                        company=lead_info.get('company', 'Unknown'),
                        task_type=self._map_activity_type(activity['type']),
                        priority=priority,
                        due_date=datetime.fromisoformat(activity['due_date'].replace('Z', '+00:00')),
                        status='upcoming',
                        description=activity['description'] or activity['subject'],
                        contact_history=contact_history,
                        engagement_level=engagement_level,
                        recommended_action=self._generate_recommended_action(
                            activity, lead_info, contact_history, engagement_level
                        ),
                        context={
                            'days_until_due': (datetime.fromisoformat(activity['due_date'].replace('Z', '+00:00')) - 
                                             datetime.now(timezone.utc)).days,
                            'lead_score': lead_info.get('lead_score', 0),
                            'last_contact_days': self._days_since_last_contact(contact_history)
                        }
                    )
                    tasks.append(task)
                
                return tasks
            
            return []
            
        except Exception as e:
            print(f"Error getting upcoming follow-ups: {e}")
            return []
    
    def create_follow_up_sequence(self, lead_id: str, sequence_type: str, 
                                 user_id: str, organization_id: str) -> bool:
        """
        Create an automated follow-up sequence for a lead
        """
        try:
            # Get sequence template
            template = self._get_sequence_template(sequence_type)
            if not template:
                return False
            
            # Get lead information
            lead_info = self._get_lead_details(lead_id)
            if not lead_info:
                return False
            
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Create activities for each step in the sequence
            sequence_id = f"seq_{lead_id}_{int(datetime.now().timestamp())}"
            
            for i, step in enumerate(template['steps']):
                due_date = datetime.now() + timedelta(days=step['delay_days'])
                
                activity_data = {
                    'type': step['type'],
                    'subject': step['subject'].format(
                        lead_name=lead_info.get('name', ''),
                        company=lead_info.get('company', '')
                    ),
                    'description': step['description'].format(
                        lead_name=lead_info.get('name', ''),
                        company=lead_info.get('company', '')
                    ),
                    'status': 'planned',
                    'priority': step.get('priority', 'medium'),
                    'due_date': due_date.isoformat(),
                    'lead_id': lead_id,
                    'assigned_to': user_id,
                    'organization_id': organization_id,
                    'attachments': {
                        'sequence_id': sequence_id,
                        'sequence_step': i + 1,
                        'template': step.get('template', ''),
                        'auto_generated': True
                    }
                }
                
                response = requests.post(
                    f"{self.supabase_url}/rest/v1/activities",
                    headers=headers,
                    json=activity_data
                )
                
                if response.status_code != 201:
                    print(f"Error creating activity for step {i+1}: {response.text}")
            
            # Update lead with sequence information
            self._update_lead_sequence_info(lead_id, sequence_id, sequence_type)
            
            return True
            
        except Exception as e:
            print(f"Error creating follow-up sequence: {e}")
            return False
    
    def smart_follow_up_suggestions(self, lead_id: str) -> List[Dict]:
        """
        Generate AI-powered follow-up suggestions based on lead behavior and history
        """
        try:
            lead_info = self._get_lead_details(lead_id)
            contact_history = self._get_contact_history(lead_id)
            engagement_level = self._assess_engagement_level(contact_history)
            
            suggestions = []
            
            # Rule-based suggestions
            suggestions.extend(self._rule_based_suggestions(lead_info, contact_history, engagement_level))
            
            # AI-powered suggestions
            if self.openai_client:
                ai_suggestions = self._ai_follow_up_suggestions(lead_info, contact_history, engagement_level)
                suggestions.extend(ai_suggestions)
            
            # Remove duplicates and prioritize
            unique_suggestions = []
            seen_types = set()
            
            for suggestion in suggestions:
                if suggestion['type'] not in seen_types:
                    unique_suggestions.append(suggestion)
                    seen_types.add(suggestion['type'])
            
            return unique_suggestions[:5]  # Top 5 suggestions
            
        except Exception as e:
            print(f"Error generating follow-up suggestions: {e}")
            return []
    
    def _rule_based_suggestions(self, lead_info: Dict, contact_history: List[Dict], 
                               engagement_level: LeadEngagementLevel) -> List[Dict]:
        """Generate rule-based follow-up suggestions"""
        suggestions = []
        
        last_contact_days = self._days_since_last_contact(contact_history)
        lead_score = lead_info.get('lead_score', 0)
        
        # High-value lead suggestions
        if lead_score >= 80:
            if last_contact_days > 3:
                suggestions.append({
                    'type': 'urgent_call',
                    'title': 'Urgent: High-value lead follow-up',
                    'description': f"High-scoring lead ({lead_score}) hasn't been contacted in {last_contact_days} days",
                    'recommended_action': 'Schedule a call within 24 hours',
                    'priority': 'urgent',
                    'reasoning': 'High lead score indicates strong potential'
                })
        
        # Engagement-based suggestions
        if engagement_level == LeadEngagementLevel.RESPONSIVE:
            suggestions.append({
                'type': 'meeting_request',
                'title': 'Schedule demo or discovery call',
                'description': 'Lead is highly engaged - perfect time for a meeting',
                'recommended_action': 'Send meeting invitation with calendar link',
                'priority': 'high',
                'reasoning': 'Strong engagement pattern detected'
            })
        
        elif engagement_level == LeadEngagementLevel.UNRESPONSIVE:
            if last_contact_days > 14:
                suggestions.append({
                    'type': 'breakup_email',
                    'title': 'Send breakup email sequence',
                    'description': 'Lead unresponsive - try final engagement attempt',
                    'recommended_action': 'Send "Is this still a priority?" email',
                    'priority': 'medium',
                    'reasoning': 'Long period of non-engagement'
                })
        
        # Time-based suggestions
        if last_contact_days >= 7:
            suggestions.append({
                'type': 'value_add_email',
                'title': 'Send value-add content',
                'description': f'No contact in {last_contact_days} days - share relevant insights',
                'recommended_action': 'Send industry report or case study',
                'priority': 'medium',
                'reasoning': 'Maintain relationship with valuable content'
            })
        
        return suggestions
    
    def _ai_follow_up_suggestions(self, lead_info: Dict, contact_history: List[Dict], 
                                 engagement_level: LeadEngagementLevel) -> List[Dict]:
        """Generate AI-powered follow-up suggestions"""
        if not self.openai_client:
            return []
        
        try:
            # Prepare context for AI
            context = {
                'lead_name': lead_info.get('name', 'Unknown'),
                'company': lead_info.get('company', 'Unknown'),
                'lead_score': lead_info.get('lead_score', 0),
                'industry': lead_info.get('industry', 'Unknown'),
                'engagement_level': engagement_level.value,
                'contact_count': len(contact_history),
                'last_contact_days': self._days_since_last_contact(contact_history),
                'recent_activities': contact_history[:3] if contact_history else []
            }
            
            prompt = f"""
            As an expert sales AI assistant, analyze this lead and suggest the best follow-up approach:
            
            Lead: {context['lead_name']} at {context['company']}
            Lead Score: {context['lead_score']}/100
            Industry: {context['industry']}
            Engagement Level: {context['engagement_level']}
            Total Contacts: {context['contact_count']}
            Days Since Last Contact: {context['last_contact_days']}
            
            Recent Activity Summary:
            {json.dumps(context['recent_activities'], indent=2)}
            
            Provide 2-3 specific, actionable follow-up suggestions with reasoning.
            Focus on personalization and timing.
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert sales follow-up strategist."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response into structured suggestions
            return self._parse_ai_suggestions(ai_response)
            
        except Exception as e:
            print(f"Error generating AI suggestions: {e}")
            return []
    
    def _get_lead_details(self, lead_id: str) -> Optional[Dict]:
        """Get detailed lead information"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/leads?id=eq.{lead_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    lead = data[0]
                    return {
                        'id': lead['id'],
                        'name': f"{lead['first_name']} {lead['last_name']}",
                        'company': lead['company'],
                        'email': lead['email'],
                        'phone': lead['phone'],
                        'lead_score': lead['lead_score'],
                        'status': lead['status'],
                        'industry': lead.get('industry'),
                        'lead_source': lead.get('lead_source'),
                        'last_contacted': lead.get('last_contacted'),
                        'next_follow_up': lead.get('next_follow_up')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting lead details: {e}")
            return None
    
    def _get_contact_history(self, lead_id: str, limit: int = 10) -> List[Dict]:
        """Get contact history for a lead"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/activities",
                headers=headers,
                params={
                    'lead_id': f'eq.{lead_id}',
                    'status': 'eq.completed',
                    'order': 'completed_date.desc',
                    'limit': limit
                }
            )
            
            if response.status_code == 200:
                activities = response.json()
                return [
                    {
                        'type': activity['type'],
                        'subject': activity['subject'],
                        'date': activity['completed_date'],
                        'outcome': activity.get('outcome'),
                        'duration': activity.get('duration_minutes'),
                        'notes': activity.get('description')
                    }
                    for activity in activities
                ]
            
            return []
            
        except Exception as e:
            print(f"Error getting contact history: {e}")
            return []
    
    def _assess_engagement_level(self, contact_history: List[Dict]) -> LeadEngagementLevel:
        """Assess lead engagement level based on contact history"""
        if not contact_history:
            return LeadEngagementLevel.COLD
        
        # Count positive engagement indicators
        positive_outcomes = 0
        total_contacts = len(contact_history)
        
        for contact in contact_history:
            outcome = contact.get('outcome', '').lower()
            if any(word in outcome for word in ['interested', 'positive', 'meeting', 'demo', 'proposal']):
                positive_outcomes += 1
        
        # Calculate engagement ratio
        if total_contacts == 0:
            return LeadEngagementLevel.COLD
        
        engagement_ratio = positive_outcomes / total_contacts
        
        # Determine engagement level
        if engagement_ratio >= 0.7:
            return LeadEngagementLevel.RESPONSIVE
        elif engagement_ratio >= 0.4:
            return LeadEngagementLevel.HOT
        elif engagement_ratio >= 0.2:
            return LeadEngagementLevel.WARM
        elif any('no response' in contact.get('outcome', '').lower() for contact in contact_history):
            return LeadEngagementLevel.UNRESPONSIVE
        else:
            return LeadEngagementLevel.COLD
    
    def _days_since_last_contact(self, contact_history: List[Dict]) -> int:
        """Calculate days since last contact"""
        if not contact_history:
            return 999
        
        try:
            last_contact_date = contact_history[0]['date']
            last_contact = datetime.fromisoformat(last_contact_date.replace('Z', '+00:00'))
            return (datetime.now(timezone.utc) - last_contact).days
        except:
            return 999
    
    def _map_activity_type(self, activity_type: str) -> FollowUpType:
        """Map activity type to follow-up type"""
        mapping = {
            'call': FollowUpType.FOLLOW_UP_CALL,
            'email': FollowUpType.EMAIL_FOLLOW_UP,
            'follow_up': FollowUpType.FOLLOW_UP_CALL,
            'demo': FollowUpType.DEMO_FOLLOW_UP,
            'proposal_sent': FollowUpType.PROPOSAL_FOLLOW_UP,
            'meeting': FollowUpType.DECISION_FOLLOW_UP
        }
        return mapping.get(activity_type, FollowUpType.FOLLOW_UP_CALL)
    
    def _calculate_task_priority(self, activity: Dict, lead_info: Dict, 
                                contact_history: List[Dict], 
                                engagement_level: LeadEngagementLevel) -> FollowUpPriority:
        """Calculate task priority based on multiple factors"""
        priority_score = 0
        
        # Lead score factor
        lead_score = lead_info.get('lead_score', 0)
        if lead_score >= 80:
            priority_score += 3
        elif lead_score >= 60:
            priority_score += 2
        elif lead_score >= 40:
            priority_score += 1
        
        # Engagement level factor
        if engagement_level == LeadEngagementLevel.RESPONSIVE:
            priority_score += 3
        elif engagement_level == LeadEngagementLevel.HOT:
            priority_score += 2
        elif engagement_level == LeadEngagementLevel.WARM:
            priority_score += 1
        
        # Activity priority factor
        activity_priority = activity.get('priority', 'medium')
        if activity_priority == 'urgent':
            priority_score += 2
        elif activity_priority == 'high':
            priority_score += 1
        
        # Convert score to priority enum
        if priority_score >= 6:
            return FollowUpPriority.URGENT
        elif priority_score >= 4:
            return FollowUpPriority.HIGH
        elif priority_score >= 2:
            return FollowUpPriority.MEDIUM
        else:
            return FollowUpPriority.LOW
    
    def _generate_recommended_action(self, activity: Dict, lead_info: Dict, 
                                   contact_history: List[Dict], 
                                   engagement_level: LeadEngagementLevel) -> str:
        """Generate recommended action for a follow-up task"""
        last_contact_days = self._days_since_last_contact(contact_history)
        lead_score = lead_info.get('lead_score', 0)
        
        if engagement_level == LeadEngagementLevel.RESPONSIVE and lead_score >= 70:
            return "Priority call - lead is highly engaged and qualified"
        elif engagement_level == LeadEngagementLevel.UNRESPONSIVE and last_contact_days > 14:
            return "Send breakup email sequence or try different communication channel"
        elif activity['type'] == 'email' and last_contact_days <= 3:
            return "Share valuable content or industry insights"
        elif activity['type'] == 'call' and lead_score >= 60:
            return "Discovery call to understand needs and timeline"
        else:
            return "Standard follow-up - maintain relationship and gather information"
    
    def _get_sequence_template(self, sequence_type: str) -> Optional[Dict]:
        """Get follow-up sequence template"""
        templates = {
            'new_lead': {
                'name': 'New Lead Nurture Sequence',
                'steps': [
                    {
                        'delay_days': 0,
                        'type': 'email',
                        'subject': 'Welcome {lead_name} - Let\'s connect!',
                        'description': 'Initial welcome email with value proposition',
                        'priority': 'high',
                        'template': 'new_lead_welcome'
                    },
                    {
                        'delay_days': 2,
                        'type': 'call',
                        'subject': 'Follow-up call with {lead_name}',
                        'description': 'Discovery call to understand needs',
                        'priority': 'medium',
                        'template': 'discovery_call'
                    },
                    {
                        'delay_days': 5,
                        'type': 'email',
                        'subject': 'Valuable insights for {company}',
                        'description': 'Share relevant case study or industry report',
                        'priority': 'medium',
                        'template': 'value_add_content'
                    },
                    {
                        'delay_days': 10,
                        'type': 'call',
                        'subject': 'Check-in call with {lead_name}',
                        'description': 'Follow-up call to discuss next steps',
                        'priority': 'medium',
                        'template': 'followup_call'
                    }
                ]
            },
            'demo_followup': {
                'name': 'Post-Demo Follow-up Sequence',
                'steps': [
                    {
                        'delay_days': 1,
                        'type': 'email',
                        'subject': 'Thank you for your time, {lead_name}',
                        'description': 'Thank you email with demo recap and next steps',
                        'priority': 'high',
                        'template': 'demo_thank_you'
                    },
                    {
                        'delay_days': 3,
                        'type': 'call',
                        'subject': 'Follow-up call after demo',
                        'description': 'Address questions and discuss implementation',
                        'priority': 'high',
                        'template': 'demo_followup_call'
                    },
                    {
                        'delay_days': 7,
                        'type': 'proposal_sent',
                        'subject': 'Proposal for {company}',
                        'description': 'Send customized proposal based on demo discussion',
                        'priority': 'urgent',
                        'template': 'proposal_creation'
                    }
                ]
            }
        }
        
        return templates.get(sequence_type)
    
    def _update_lead_sequence_info(self, lead_id: str, sequence_id: str, sequence_type: str):
        """Update lead with sequence information"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            update_data = {
                'tags': f"sequence:{sequence_type}",
                'notes': f"Enrolled in {sequence_type} sequence (ID: {sequence_id})"
            }
            
            requests.patch(
                f"{self.supabase_url}/rest/v1/leads?id=eq.{lead_id}",
                headers=headers,
                json=update_data
            )
            
        except Exception as e:
            print(f"Error updating lead sequence info: {e}")
    
    def _ai_prioritize_tasks(self, tasks: List[FollowUpTask]) -> List[FollowUpTask]:
        """Use AI to prioritize tasks"""
        # This would use AI to analyze task context and reorder
        # For now, return tasks as-is
        return tasks
    
    def _parse_ai_suggestions(self, ai_response: str) -> List[Dict]:
        """Parse AI response into structured suggestions"""
        suggestions = []
        
        # Simple parsing - in production, use more sophisticated NLP
        lines = ai_response.split('\n')
        current_suggestion = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '-', '•')):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {
                    'type': 'ai_suggestion',
                    'title': line,
                    'description': line,
                    'priority': 'medium',
                    'reasoning': 'AI-generated based on lead analysis'
                }
            elif current_suggestion and line:
                current_suggestion['description'] += f" {line}"
        
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        return suggestions[:3]  # Limit to 3 AI suggestions

# Example usage and testing
if __name__ == "__main__":
    manager = AgentSDRFollowUpManager()
    
    # Test follow-up queue
    test_user_id = "test-user-123"
    test_org_id = "test-org-456"
    
    print("Getting follow-up queue...")
    queue = manager.get_follow_up_queue(test_user_id, test_org_id)
    
    print(f"Found {len(queue)} follow-up tasks")
    for task in queue[:5]:
        print(f"- {task.lead_name} ({task.company}) - {task.task_type.value} - {task.priority.value}")
    
    # Test follow-up suggestions
    if queue:
        test_lead_id = queue[0].lead_id
        print(f"\nGetting suggestions for lead: {test_lead_id}")
        suggestions = manager.smart_follow_up_suggestions(test_lead_id)
        
        for suggestion in suggestions:
            print(f"- {suggestion['title']}: {suggestion['description']}")