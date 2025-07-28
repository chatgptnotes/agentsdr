"""
AgentSDR Meeting Preparation Intelligence Center
AI-powered meeting preparation with context, talking points, and strategic recommendations
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from dotenv import load_dotenv

load_dotenv()

class MeetingType(Enum):
    DISCOVERY = "discovery"
    DEMO = "demo"
    PROPOSAL_PRESENTATION = "proposal_presentation"
    NEGOTIATION = "negotiation"
    CHECK_IN = "check_in"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"

class AttendeeRole(Enum):
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"
    USER = "user"
    TECHNICAL = "technical"
    PROCUREMENT = "procurement"
    UNKNOWN = "unknown"

@dataclass
class MeetingAttendee:
    name: str
    title: str
    role: AttendeeRole
    email: Optional[str]
    background: Optional[str]
    interests: List[str]
    concerns: List[str]
    influence_level: int  # 1-10 scale

@dataclass
class TalkingPoint:
    topic: str
    key_message: str
    supporting_details: List[str]
    potential_objections: List[str]
    success_metrics: List[str]
    priority: int  # 1-5 scale

@dataclass
class MeetingBriefing:
    meeting_id: str
    meeting_type: MeetingType
    meeting_date: datetime
    duration_minutes: int
    attendees: List[MeetingAttendee]
    primary_objectives: List[str]
    talking_points: List[TalkingPoint]
    potential_questions: List[Dict]
    competitive_landscape: Dict
    historical_context: Dict
    recommended_agenda: List[Dict]
    success_criteria: List[str]
    risk_factors: List[str]
    follow_up_actions: List[str]

class AgentSDRMeetingPrep:
    """
    Comprehensive meeting preparation system that provides sales representatives
    with context, talking points, and strategic recommendations for client meetings
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.openai_client = None
        
        if os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_client = openai
        
        # Question banks by meeting type
        self.question_banks = {
            MeetingType.DISCOVERY: [
                "What are your biggest challenges in [relevant area]?",
                "How are you currently handling [specific process]?",
                "What would success look like for you?",
                "Who else is involved in this decision?",
                "What's your timeline for making a decision?",
                "What's driving the urgency for a solution?",
                "How do you measure success in this area?",
                "What solutions have you evaluated so far?"
            ],
            MeetingType.DEMO: [
                "Which features are most important to you?",
                "How would this integrate with your current systems?",
                "What questions do you have about the functionality?",
                "How do you see your team using this?",
                "What concerns do you have about implementation?",
                "How does this compare to what you're using now?"
            ],
            MeetingType.PROPOSAL_PRESENTATION: [
                "Does this address your key requirements?",
                "What questions do you have about the pricing?",
                "How does the timeline work for you?",
                "What concerns does your team have?",
                "What would need to change for this to be perfect?",
                "Who else needs to review this?"
            ]
        }
        
        # Objection handling templates
        self.objection_handlers = {
            'price_too_high': {
                'response': "I understand price is a concern. Let's look at the ROI...",
                'follow_up': "What's your target payback period?",
                'value_points': ['Cost savings', 'Efficiency gains', 'Risk reduction']
            },
            'need_to_think': {
                'response': "Of course, this is an important decision. What specific areas would you like to think through?",
                'follow_up': "What additional information would be helpful?",
                'value_points': ['Risk mitigation', 'Implementation support', 'Success guarantee']
            },
            'not_the_right_time': {
                'response': "I understand timing is crucial. What would need to change for the timing to be right?",
                'follow_up': "What are you prioritizing right now?",
                'value_points': ['Phased implementation', 'Quick wins', 'Future planning']
            }
        }
    
    def generate_meeting_briefing(self, meeting_id: str, opportunity_id: str,
                                 meeting_type: MeetingType) -> Optional[MeetingBriefing]:
        """
        Generate comprehensive meeting briefing with AI-enhanced insights
        """
        try:
            # Get meeting details
            meeting_data = self._get_meeting_data(meeting_id)
            if not meeting_data:
                return None
            
            # Get opportunity and lead context
            opportunity = self._get_opportunity_data(opportunity_id)
            lead = self._get_lead_data(opportunity['lead_id']) if opportunity else None
            
            if not opportunity or not lead:
                return None
            
            # Get attendee information
            attendees = self._prepare_attendee_profiles(meeting_data.get('attendees', []))
            
            # Get historical context
            historical_context = self._get_historical_context(opportunity_id, lead['id'])
            
            # Generate talking points
            talking_points = self._generate_talking_points(
                meeting_type, opportunity, lead, historical_context
            )
            
            # Generate potential questions
            potential_questions = self._prepare_potential_questions(meeting_type, opportunity, lead)
            
            # Get competitive landscape
            competitive_landscape = self._get_competitive_context(opportunity_id)
            
            # Generate recommended agenda
            recommended_agenda = self._create_meeting_agenda(meeting_type, meeting_data, talking_points)
            
            # AI enhancement if available
            if self.openai_client:
                enhanced_briefing = self._ai_enhance_briefing(
                    meeting_type, opportunity, lead, attendees, talking_points
                )
                if enhanced_briefing:
                    talking_points.extend(enhanced_briefing.get('additional_points', []))
                    potential_questions.extend(enhanced_briefing.get('strategic_questions', []))
            
            # Create comprehensive briefing
            briefing = MeetingBriefing(
                meeting_id=meeting_id,
                meeting_type=meeting_type,
                meeting_date=datetime.fromisoformat(meeting_data['scheduled_time'].replace('Z', '+00:00')),
                duration_minutes=meeting_data.get('duration_minutes', 60),
                attendees=attendees,
                primary_objectives=self._define_meeting_objectives(meeting_type, opportunity),
                talking_points=talking_points,
                potential_questions=potential_questions,
                competitive_landscape=competitive_landscape,
                historical_context=historical_context,
                recommended_agenda=recommended_agenda,
                success_criteria=self._define_success_criteria(meeting_type, opportunity),
                risk_factors=self._identify_meeting_risks(meeting_type, opportunity, historical_context),
                follow_up_actions=self._suggest_follow_up_actions(meeting_type, opportunity)
            )
            
            # Save briefing to database
            self._save_meeting_briefing(briefing)
            
            return briefing
            
        except Exception as e:
            print(f"Error generating meeting briefing: {e}")
            return None
    
    def _prepare_attendee_profiles(self, attendee_data: List[Dict]) -> List[MeetingAttendee]:
        """Prepare detailed attendee profiles with background research"""
        attendees = []
        
        for attendee_info in attendee_data:
            # Determine role based on title
            role = self._determine_attendee_role(attendee_info.get('title', ''))
            
            # Get background information (would integrate with LinkedIn, company research, etc.)
            background = self._research_attendee_background(attendee_info)
            
            attendee = MeetingAttendee(
                name=attendee_info.get('name', 'Unknown'),
                title=attendee_info.get('title', 'Unknown'),
                role=role,
                email=attendee_info.get('email'),
                background=background.get('summary'),
                interests=background.get('interests', []),
                concerns=background.get('concerns', []),
                influence_level=self._assess_influence_level(attendee_info.get('title', ''), role)
            )
            
            attendees.append(attendee)
        
        return attendees
    
    def _generate_talking_points(self, meeting_type: MeetingType, opportunity: Dict,
                                lead: Dict, historical_context: Dict) -> List[TalkingPoint]:
        """Generate strategic talking points based on context"""
        talking_points = []
        
        # Company-specific value proposition
        if meeting_type == MeetingType.DISCOVERY:
            talking_points.append(TalkingPoint(
                topic="Company Background & Challenges",
                key_message=f"Understanding {lead['company']}'s unique challenges in {lead.get('industry', 'your industry')}",
                supporting_details=[
                    f"Research shows companies in {lead.get('industry', 'your industry')} face specific challenges",
                    "We've helped similar companies achieve measurable results",
                    "Our approach is tailored to your industry requirements"
                ],
                potential_objections=[
                    "We're different from other companies",
                    "Our situation is unique",
                    "We've tried solutions before"
                ],
                success_metrics=[
                    "Clear understanding of pain points",
                    "Identified decision criteria",
                    "Established timeline and budget"
                ],
                priority=5
            ))
        
        elif meeting_type == MeetingType.DEMO:
            talking_points.append(TalkingPoint(
                topic="Solution Demonstration",
                key_message="How our solution directly addresses your specific requirements",
                supporting_details=[
                    f"Customized demo based on {lead['company']}'s use case",
                    "Integration capabilities with existing systems",
                    "ROI examples from similar implementations"
                ],
                potential_objections=[
                    "Too complex for our team",
                    "Integration concerns",
                    "Training requirements"
                ],
                success_metrics=[
                    "Positive feedback on functionality",
                    "Technical questions answered",
                    "Next steps agreed upon"
                ],
                priority=5
            ))
        
        elif meeting_type == MeetingType.PROPOSAL_PRESENTATION:
            talking_points.append(TalkingPoint(
                topic="Proposal Overview",
                key_message=f"Comprehensive solution designed specifically for {lead['company']}",
                supporting_details=[
                    "Addresses all key requirements identified",
                    "Phased implementation approach",
                    "Clear ROI projections and success metrics"
                ],
                potential_objections=[
                    "Price concerns",
                    "Implementation timeline",
                    "Risk mitigation"
                ],
                success_metrics=[
                    "Proposal acceptance",
                    "Contract negotiation initiated",
                    "Clear next steps defined"
                ],
                priority=5
            ))
        
        # Add competitive differentiation point
        if historical_context.get('competitors_mentioned'):
            talking_points.append(TalkingPoint(
                topic="Competitive Advantages",
                key_message="Why we're the best fit for your specific needs",
                supporting_details=[
                    "Industry-specific expertise",
                    "Proven track record with similar companies",
                    "Superior support and implementation process"
                ],
                potential_objections=[
                    "Other vendors seem similar",
                    "Competitor has lower price",
                    "Existing relationship with competitor"
                ],
                success_metrics=[
                    "Clear differentiation understood",
                    "Competitive concerns addressed",
                    "Preference established"
                ],
                priority=4
            ))
        
        # Add ROI-focused talking point
        if opportunity.get('value', 0) > 50000:
            talking_points.append(TalkingPoint(
                topic="Return on Investment",
                key_message="Quantifiable business impact and ROI",
                supporting_details=[
                    f"Projected annual savings: ${opportunity.get('value', 0) * 0.3:,.0f}",
                    "Payback period: 6-12 months",
                    "Long-term value creation opportunities"
                ],
                potential_objections=[
                    "ROI projections seem optimistic",
                    "Hidden costs not considered",
                    "Implementation risks"
                ],
                success_metrics=[
                    "ROI methodology accepted",
                    "Business case strengthened",
                    "Financial justification clear"
                ],
                priority=4
            ))
        
        return talking_points
    
    def _prepare_potential_questions(self, meeting_type: MeetingType, 
                                   opportunity: Dict, lead: Dict) -> List[Dict]:
        """Prepare potential questions client might ask"""
        questions = []
        
        # Get base questions for meeting type
        base_questions = self.question_banks.get(meeting_type, [])
        
        for question in base_questions:
            # Personalize questions with company/industry context
            personalized_question = question.replace('[relevant area]', lead.get('industry', 'your industry'))
            personalized_question = personalized_question.replace('[specific process]', 'your current process')
            
            questions.append({
                'question': personalized_question,
                'category': 'discovery',
                'priority': 'high',
                'suggested_follow_up': self._get_follow_up_question(personalized_question)
            })
        
        # Add context-specific questions
        if lead.get('industry'):
            questions.append({
                'question': f"How do you handle {lead['industry']}-specific regulations?",
                'category': 'compliance',
                'priority': 'medium',
                'suggested_follow_up': "What compliance challenges are you facing?"
            })
        
        if opportunity.get('stage') == 'proposal':
            questions.extend([
                {
                    'question': "What's your decision-making process?",
                    'category': 'process',
                    'priority': 'high',
                    'suggested_follow_up': "Who else is involved in the evaluation?"
                },
                {
                    'question': "What's your timeline for implementation?",
                    'category': 'timeline',
                    'priority': 'high',
                    'suggested_follow_up': "What would accelerate or delay the timeline?"
                }
            ])
        
        return questions
    
    def _ai_enhance_briefing(self, meeting_type: MeetingType, opportunity: Dict,
                           lead: Dict, attendees: List[MeetingAttendee],
                           talking_points: List[TalkingPoint]) -> Optional[Dict]:
        """Use AI to enhance meeting briefing with strategic insights"""
        if not self.openai_client:
            return None
        
        try:
            # Prepare context for AI
            context = {
                'meeting_type': meeting_type.value,
                'company': lead.get('company', 'Unknown'),
                'industry': lead.get('industry', 'Unknown'),
                'opportunity_stage': opportunity.get('stage', 'Unknown'),
                'opportunity_value': opportunity.get('value', 0),
                'attendees': [{'name': a.name, 'title': a.title, 'role': a.role.value} for a in attendees],
                'key_topics': [tp.topic for tp in talking_points]
            }
            
            prompt = f"""
            As an expert sales strategist, enhance this meeting preparation for a {context['meeting_type']} meeting:
            
            Company: {context['company']} ({context['industry']})
            Opportunity: {context['opportunity_stage']} stage, ${context['opportunity_value']:,.2f}
            
            Meeting Attendees:
            {json.dumps(context['attendees'], indent=2)}
            
            Current Talking Points:
            {json.dumps(context['key_topics'], indent=2)}
            
            Provide strategic enhancements:
            1. 2-3 additional high-impact talking points
            2. 3-4 strategic questions to ask
            3. Potential objections and responses
            4. Meeting success tactics
            
            Focus on:
            - Industry-specific insights
            - Attendee-specific messaging
            - Competitive positioning
            - Risk mitigation
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sales strategist with 20+ years of experience in B2B sales."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            ai_enhancement = response.choices[0].message.content.strip()
            
            # Parse AI response into structured format
            return self._parse_ai_enhancement(ai_enhancement)
            
        except Exception as e:
            print(f"Error generating AI enhancement: {e}")
            return None
    
    def generate_post_meeting_summary(self, meeting_id: str, meeting_notes: str,
                                    outcomes: List[str]) -> Dict:
        """Generate post-meeting summary and next steps"""
        try:
            # Get original meeting briefing
            briefing = self._get_meeting_briefing(meeting_id)
            if not briefing:
                return {}
            
            # Analyze meeting success against criteria
            success_analysis = self._analyze_meeting_success(
                briefing['success_criteria'], outcomes
            )
            
            # Generate next steps based on outcomes
            next_steps = self._generate_next_steps(
                briefing['meeting_type'], outcomes, briefing['opportunity_id']
            )
            
            # AI-powered analysis if available
            ai_analysis = {}
            if self.openai_client:
                ai_analysis = self._ai_analyze_meeting_outcomes(
                    briefing, meeting_notes, outcomes
                )
            
            summary = {
                'meeting_id': meeting_id,
                'meeting_date': briefing['meeting_date'],
                'success_score': success_analysis['score'],
                'objectives_met': success_analysis['objectives_met'],
                'key_outcomes': outcomes,
                'next_steps': next_steps,
                'risks_identified': ai_analysis.get('risks', []),
                'opportunities_identified': ai_analysis.get('opportunities', []),
                'recommended_follow_up': ai_analysis.get('follow_up_strategy', ''),
                'updated_deal_probability': ai_analysis.get('probability_update'),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Save summary to database
            self._save_meeting_summary(summary)
            
            return summary
            
        except Exception as e:
            print(f"Error generating post-meeting summary: {e}")
            return {}
    
    # Helper methods for data retrieval and processing
    def _get_meeting_data(self, meeting_id: str) -> Optional[Dict]:
        """Get meeting data from database"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/activities?id=eq.{meeting_id}&type=eq.meeting",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            
            return None
        except Exception as e:
            print(f"Error getting meeting data: {e}")
            return None
    
    def _determine_attendee_role(self, title: str) -> AttendeeRole:
        """Determine attendee role based on title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['ceo', 'president', 'founder', 'owner', 'director', 'vp']):
            return AttendeeRole.DECISION_MAKER
        elif any(word in title_lower for word in ['manager', 'lead', 'head', 'supervisor']):
            return AttendeeRole.INFLUENCER
        elif any(word in title_lower for word in ['engineer', 'developer', 'architect', 'tech']):
            return AttendeeRole.TECHNICAL
        elif any(word in title_lower for word in ['procurement', 'purchasing', 'buyer']):
            return AttendeeRole.PROCUREMENT
        elif any(word in title_lower for word in ['user', 'specialist', 'coordinator']):
            return AttendeeRole.USER
        else:
            return AttendeeRole.UNKNOWN
    
    def _assess_influence_level(self, title: str, role: AttendeeRole) -> int:
        """Assess influence level of attendee (1-10 scale)"""
        base_scores = {
            AttendeeRole.DECISION_MAKER: 9,
            AttendeeRole.INFLUENCER: 7,
            AttendeeRole.TECHNICAL: 6,
            AttendeeRole.PROCUREMENT: 5,
            AttendeeRole.USER: 4,
            AttendeeRole.UNKNOWN: 3
        }
        
        base_score = base_scores.get(role, 3)
        
        # Adjust based on title seniority
        title_lower = title.lower()
        if any(word in title_lower for word in ['ceo', 'president', 'founder']):
            base_score = 10
        elif any(word in title_lower for word in ['cto', 'cfo', 'coo', 'vp']):
            base_score = max(base_score, 8)
        elif 'director' in title_lower:
            base_score = max(base_score, 7)
        elif 'senior' in title_lower:
            base_score = max(base_score, base_score + 1)
        
        return min(10, base_score)
    
    # Additional helper methods would be implemented here...

# Example usage and testing
if __name__ == "__main__":
    meeting_prep = AgentSDRMeetingPrep()
    
    # Test meeting briefing generation
    test_meeting_id = "meeting-123"
    test_opportunity_id = "opp-456"
    
    print("Generating meeting briefing...")
    briefing = meeting_prep.generate_meeting_briefing(
        test_meeting_id, 
        test_opportunity_id, 
        MeetingType.DISCOVERY
    )
    
    if briefing:
        print(f"Meeting briefing generated for {briefing.meeting_type.value} meeting")
        print(f"Attendees: {len(briefing.attendees)}")
        print(f"Talking points: {len(briefing.talking_points)}")
        print(f"Potential questions: {len(briefing.potential_questions)}")
    else:
        print("Failed to generate meeting briefing")