"""
AgentSDR Opportunity Intelligence Radar
AI-powered opportunity analysis, risk assessment, and sales insights
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
import re
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

class InsightType(Enum):
    BUYING_SIGNAL = "buying_signal"
    RISK_ALERT = "risk_alert"
    COMPETITOR_MENTION = "competitor_mention"
    BUDGET_INDICATOR = "budget_indicator"
    TIMELINE_SHIFT = "timeline_shift"
    DECISION_MAKER_CHANGE = "decision_maker_change"
    ENGAGEMENT_PATTERN = "engagement_pattern"
    PRICE_SENSITIVITY = "price_sensitivity"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConfidenceLevel(Enum):
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.9

@dataclass
class OpportunityInsight:
    insight_id: str
    opportunity_id: str
    insight_type: InsightType
    title: str
    description: str
    confidence_score: float
    risk_level: RiskLevel
    recommended_actions: List[str]
    data_sources: List[str]
    created_at: datetime
    is_actionable: bool = True

@dataclass
class CompetitorAnalysis:
    competitor_name: str
    mention_count: int
    sentiment_score: float
    last_mentioned: datetime
    context_snippets: List[str]
    threat_level: RiskLevel
    recommended_response: str

@dataclass
class BuyingSignal:
    signal_type: str
    strength: float
    description: str
    source: str
    detected_at: datetime
    keywords: List[str]

class AgentSDROpportunityIntelligence:
    """
    Advanced opportunity intelligence system that analyzes communications,
    identifies patterns, and provides actionable insights for sales teams
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.openai_client = None
        
        if os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_client = openai
        
        # Buying signal patterns
        self.buying_signals = {
            'budget_approved': {
                'keywords': ['budget approved', 'funding secured', 'budget allocated', 'financial approval'],
                'strength': 0.9,
                'description': 'Budget has been approved or allocated'
            },
            'timeline_urgency': {
                'keywords': ['asap', 'urgent', 'immediately', 'by end of quarter', 'deadline'],
                'strength': 0.8,
                'description': 'Client expressing urgency in timeline'
            },
            'decision_maker_involved': {
                'keywords': ['ceo wants', 'board approved', 'management decision', 'executive team'],
                'strength': 0.85,
                'description': 'Senior decision makers are involved'
            },
            'pain_point_escalation': {
                'keywords': ['critical issue', 'major problem', 'costing us', 'losing money'],
                'strength': 0.75,
                'description': 'Pain points are escalating and need immediate solution'
            },
            'competitive_pressure': {
                'keywords': ['competitor is', 'other vendors', 'comparison', 'evaluating options'],
                'strength': 0.7,
                'description': 'Client is actively comparing solutions'
            }
        }
        
        # Risk indicators
        self.risk_indicators = {
            'no_response': {
                'pattern': 'extended_silence',
                'threshold_days': 7,
                'risk_level': RiskLevel.MEDIUM
            },
            'budget_concerns': {
                'keywords': ['expensive', 'costly', 'budget tight', 'price is high'],
                'risk_level': RiskLevel.HIGH
            },
            'competitor_preference': {
                'keywords': ['prefer', 'leaning towards', 'other solution', 'alternative'],
                'risk_level': RiskLevel.HIGH
            },
            'delayed_decisions': {
                'keywords': ['postpone', 'delay', 'push back', 'later date'],
                'risk_level': RiskLevel.MEDIUM
            }
        }
    
    def analyze_opportunity(self, opportunity_id: str) -> List[OpportunityInsight]:
        """
        Comprehensive analysis of an opportunity to generate actionable insights
        """
        try:
            # Get opportunity data
            opportunity = self._get_opportunity_data(opportunity_id)
            if not opportunity:
                return []
            
            # Get all communications and activities
            communications = self._get_opportunity_communications(opportunity_id)
            activities = self._get_opportunity_activities(opportunity_id)
            
            insights = []
            
            # Analyze buying signals
            buying_signals = self._detect_buying_signals(communications)
            for signal in buying_signals:
                insight = self._create_buying_signal_insight(opportunity_id, signal)
                if insight:
                    insights.append(insight)
            
            # Analyze risk factors
            risk_factors = self._assess_risk_factors(opportunity, communications, activities)
            for risk in risk_factors:
                insight = self._create_risk_insight(opportunity_id, risk)
                if insight:
                    insights.append(insight)
            
            # Analyze competitor mentions
            competitor_analysis = self._analyze_competitors(communications)
            for comp_insight in competitor_analysis:
                insight = self._create_competitor_insight(opportunity_id, comp_insight)
                if insight:
                    insights.append(insight)
            
            # Analyze engagement patterns
            engagement_insights = self._analyze_engagement_patterns(activities)
            for eng_insight in engagement_insights:
                insight = self._create_engagement_insight(opportunity_id, eng_insight)
                if insight:
                    insights.append(insight)
            
            # AI-powered insights if available
            if self.openai_client:
                ai_insights = self._generate_ai_insights(opportunity, communications, activities)
                insights.extend(ai_insights)
            
            # Save insights to database
            for insight in insights:
                self._save_insight(insight)
            
            return insights
            
        except Exception as e:
            print(f"Error analyzing opportunity: {e}")
            return []
    
    def _detect_buying_signals(self, communications: List[Dict]) -> List[BuyingSignal]:
        """Detect buying signals in communications"""
        signals = []
        
        for comm in communications:
            content = comm.get('content', '').lower()
            subject = comm.get('subject', '').lower()
            full_text = f"{subject} {content}"
            
            for signal_type, signal_config in self.buying_signals.items():
                for keyword in signal_config['keywords']:
                    if keyword in full_text:
                        signal = BuyingSignal(
                            signal_type=signal_type,
                            strength=signal_config['strength'],
                            description=signal_config['description'],
                            source=comm.get('type', 'unknown'),
                            detected_at=datetime.fromisoformat(comm['created_at'].replace('Z', '+00:00')),
                            keywords=[keyword]
                        )
                        signals.append(signal)
                        break  # Only count once per communication
        
        return signals
    
    def _assess_risk_factors(self, opportunity: Dict, communications: List[Dict], 
                           activities: List[Dict]) -> List[Dict]:
        """Assess various risk factors for the opportunity"""
        risks = []
        
        # Check for communication gaps
        last_activity = self._get_last_activity_date(activities)
        if last_activity:
            days_since_last_contact = (datetime.now(timezone.utc) - last_activity).days
            if days_since_last_contact > 14:
                risks.append({
                    'type': 'communication_gap',
                    'risk_level': RiskLevel.HIGH if days_since_last_contact > 21 else RiskLevel.MEDIUM,
                    'description': f'No contact for {days_since_last_contact} days',
                    'recommended_actions': ['Send follow-up email', 'Schedule check-in call', 'Provide value-add content']
                })
        
        # Check for budget concerns in communications
        budget_concerns = 0
        for comm in communications:
            content = comm.get('content', '').lower()
            for keyword in self.risk_indicators['budget_concerns']['keywords']:
                if keyword in content:
                    budget_concerns += 1
        
        if budget_concerns > 2:
            risks.append({
                'type': 'budget_concerns',
                'risk_level': RiskLevel.HIGH,
                'description': f'Budget concerns mentioned {budget_concerns} times',
                'recommended_actions': ['Prepare ROI analysis', 'Discuss pricing flexibility', 'Highlight cost savings']
            })
        
        # Check if opportunity is past expected close date
        expected_close = opportunity.get('expected_close_date')
        if expected_close:
            close_date = datetime.fromisoformat(expected_close).replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > close_date:
                days_overdue = (datetime.now(timezone.utc) - close_date).days
                risks.append({
                    'type': 'overdue_close',
                    'risk_level': RiskLevel.HIGH,
                    'description': f'Opportunity is {days_overdue} days past expected close date',
                    'recommended_actions': ['Update timeline', 'Understand delays', 'Reassess probability']
                })
        
        # Check stage progression
        stage_risk = self._assess_stage_progression_risk(opportunity, activities)
        if stage_risk:
            risks.append(stage_risk)
        
        return risks
    
    def _analyze_competitors(self, communications: List[Dict]) -> List[CompetitorAnalysis]:
        """Analyze competitor mentions in communications"""
        competitor_mentions = defaultdict(list)
        
        # Common competitor keywords
        competitor_keywords = [
            'salesforce', 'hubspot', 'zoho', 'pipedrive', 'microsoft', 
            'competitor', 'alternative', 'other vendor', 'different solution'
        ]
        
        for comm in communications:
            content = comm.get('content', '').lower()
            subject = comm.get('subject', '').lower()
            full_text = f"{subject} {content}"
            
            for keyword in competitor_keywords:
                if keyword in full_text:
                    # Extract context around the mention
                    context = self._extract_context(full_text, keyword)
                    competitor_mentions[keyword].append({
                        'context': context,
                        'date': comm['created_at'],
                        'type': comm.get('type', 'unknown')
                    })
        
        # Analyze sentiment and create competitor analysis
        analyses = []
        for competitor, mentions in competitor_mentions.items():
            if mentions:
                sentiment_score = self._analyze_competitor_sentiment(mentions)
                threat_level = self._assess_competitor_threat_level(competitor, mentions, sentiment_score)
                
                analysis = CompetitorAnalysis(
                    competitor_name=competitor.title(),
                    mention_count=len(mentions),
                    sentiment_score=sentiment_score,
                    last_mentioned=datetime.fromisoformat(mentions[-1]['date'].replace('Z', '+00:00')),
                    context_snippets=[m['context'] for m in mentions[:3]],
                    threat_level=threat_level,
                    recommended_response=self._get_competitor_response_strategy(competitor, threat_level)
                )
                analyses.append(analysis)
        
        return analyses
    
    def _analyze_engagement_patterns(self, activities: List[Dict]) -> List[Dict]:
        """Analyze engagement patterns to identify trends"""
        insights = []
        
        if not activities:
            return insights
        
        # Sort activities by date
        sorted_activities = sorted(activities, key=lambda x: x['created_at'])
        
        # Analyze response time patterns
        response_times = self._calculate_response_times(sorted_activities)
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            
            if avg_response_time < 4:  # Less than 4 hours
                insights.append({
                    'type': 'high_engagement',
                    'description': f'Client responds quickly (avg {avg_response_time:.1f} hours)',
                    'positive': True,
                    'recommended_actions': ['Maintain momentum', 'Schedule next meeting', 'Move to next stage']
                })
            elif avg_response_time > 48:  # More than 48 hours
                insights.append({
                    'type': 'low_engagement',
                    'description': f'Slow response times (avg {avg_response_time:.1f} hours)',
                    'positive': False,
                    'recommended_actions': ['Try different communication channel', 'Provide more value', 'Check interest level']
                })
        
        # Analyze activity frequency
        recent_activities = [a for a in activities if 
                           (datetime.now(timezone.utc) - 
                            datetime.fromisoformat(a['created_at'].replace('Z', '+00:00'))).days <= 30]
        
        if len(recent_activities) > 10:
            insights.append({
                'type': 'high_activity',
                'description': f'{len(recent_activities)} activities in last 30 days',
                'positive': True,
                'recommended_actions': ['Keep engagement high', 'Push for decision', 'Schedule demo or presentation']
            })
        elif len(recent_activities) < 3:
            insights.append({
                'type': 'low_activity',
                'description': f'Only {len(recent_activities)} activities in last 30 days',
                'positive': False,
                'recommended_actions': ['Increase touchpoints', 'Provide valuable content', 'Re-engage with different approach']
            })
        
        return insights
    
    def _generate_ai_insights(self, opportunity: Dict, communications: List[Dict], 
                            activities: List[Dict]) -> List[OpportunityInsight]:
        """Generate AI-powered insights"""
        if not self.openai_client:
            return []
        
        try:
            # Prepare context for AI analysis
            context = {
                'opportunity_stage': opportunity.get('stage'),
                'opportunity_value': opportunity.get('value'),
                'probability': opportunity.get('probability'),
                'expected_close_date': opportunity.get('expected_close_date'),
                'communication_count': len(communications),
                'activity_count': len(activities),
                'recent_communications': communications[-3:] if communications else [],
                'recent_activities': activities[-5:] if activities else []
            }
            
            prompt = f"""
            As an expert sales analyst, analyze this opportunity and provide specific insights:
            
            Opportunity Details:
            - Stage: {context['opportunity_stage']}
            - Value: ${context['opportunity_value']:,.2f}
            - Probability: {context['probability']}%
            - Expected Close: {context['expected_close_date']}
            
            Communication & Activity Summary:
            - Total Communications: {context['communication_count']}
            - Total Activities: {context['activity_count']}
            
            Recent Communications:
            {json.dumps(context['recent_communications'], indent=2)[:1000]}
            
            Recent Activities:
            {json.dumps(context['recent_activities'], indent=2)[:1000]}
            
            Provide 2-3 specific insights focusing on:
            1. Deal progression and momentum
            2. Potential risks or opportunities
            3. Recommended next actions
            
            Format each insight with a clear title and specific recommendations.
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sales opportunity analyst with 15+ years of experience."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response into structured insights
            return self._parse_ai_insights(opportunity['id'], ai_response)
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return []
    
    def get_opportunity_health_score(self, opportunity_id: str) -> Dict:
        """Calculate comprehensive health score for an opportunity"""
        try:
            insights = self.analyze_opportunity(opportunity_id)
            opportunity = self._get_opportunity_data(opportunity_id)
            activities = self._get_opportunity_activities(opportunity_id)
            
            if not opportunity:
                return {'health_score': 0, 'factors': []}
            
            # Calculate base score from opportunity data
            base_score = 50
            factors = []
            
            # Stage progression factor
            stage_scores = {
                'prospecting': 20,
                'qualification': 35,
                'needs_analysis': 50,
                'proposal': 70,
                'negotiation': 85,
                'closed_won': 100,
                'closed_lost': 0
            }
            
            stage = opportunity.get('stage', 'prospecting').lower()
            stage_score = stage_scores.get(stage, 20)
            base_score = stage_score
            
            # Probability factor
            probability = opportunity.get('probability', 50)
            probability_weight = 0.3
            base_score += (probability - 50) * probability_weight
            
            # Recent activity factor
            recent_activities = [a for a in activities if 
                               (datetime.now(timezone.utc) - 
                                datetime.fromisoformat(a['created_at'].replace('Z', '+00:00'))).days <= 7]
            
            if recent_activities:
                activity_boost = min(len(recent_activities) * 2, 10)
                base_score += activity_boost
                factors.append(f"Recent activity boost: +{activity_boost}")
            
            # Positive insights boost
            positive_insights = [i for i in insights if i.insight_type in [
                InsightType.BUYING_SIGNAL, InsightType.BUDGET_INDICATOR
            ]]
            
            if positive_insights:
                insight_boost = len(positive_insights) * 5
                base_score += insight_boost
                factors.append(f"Positive signals: +{insight_boost}")
            
            # Risk factors penalty
            risk_insights = [i for i in insights if i.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
            
            if risk_insights:
                risk_penalty = len(risk_insights) * 8
                base_score -= risk_penalty
                factors.append(f"Risk factors: -{risk_penalty}")
            
            # Timeline factor
            expected_close = opportunity.get('expected_close_date')
            if expected_close:
                close_date = datetime.fromisoformat(expected_close).replace(tzinfo=timezone.utc)
                days_to_close = (close_date - datetime.now(timezone.utc)).days
                
                if days_to_close < 0:
                    base_score -= 15
                    factors.append("Past due date: -15")
                elif days_to_close < 30:
                    base_score += 5
                    factors.append("Closing soon: +5")
            
            # Ensure score is within bounds
            final_score = max(0, min(100, base_score))
            
            # Determine health status
            if final_score >= 80:
                health_status = "Excellent"
            elif final_score >= 65:
                health_status = "Good"
            elif final_score >= 50:
                health_status = "Fair"
            elif final_score >= 35:
                health_status = "Poor"
            else:
                health_status = "Critical"
            
            return {
                'health_score': round(final_score, 1),
                'health_status': health_status,
                'factors': factors,
                'recommendation': self._get_health_recommendation(final_score, insights),
                'calculated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating health score: {e}")
            return {'health_score': 0, 'factors': []}
    
    # Helper methods for data retrieval and processing
    def _get_opportunity_data(self, opportunity_id: str) -> Optional[Dict]:
        """Get opportunity data from database"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/opportunities?id=eq.{opportunity_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            
            return None
        except Exception as e:
            print(f"Error getting opportunity data: {e}")
            return None
    
    def _get_opportunity_communications(self, opportunity_id: str) -> List[Dict]:
        """Get communications related to the opportunity"""
        # This would integrate with email systems, CRM, etc.
        # For now, return empty list as placeholder
        return []
    
    def _get_opportunity_activities(self, opportunity_id: str) -> List[Dict]:
        """Get activities related to the opportunity"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.supabase_url}/rest/v1/activities?opportunity_id=eq.{opportunity_id}&order=created_at.desc",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            
            return []
        except Exception as e:
            print(f"Error getting activities: {e}")
            return []
    
    # Additional helper methods would be implemented here...
    # Including insight creation, saving, parsing, etc.

# Example usage and testing
if __name__ == "__main__":
    intelligence = AgentSDROpportunityIntelligence()
    
    # Test opportunity analysis
    test_opportunity_id = "test-opp-123"
    
    print("Analyzing opportunity...")
    insights = intelligence.analyze_opportunity(test_opportunity_id)
    
    print(f"Generated {len(insights)} insights:")
    for insight in insights:
        print(f"- {insight.title}: {insight.description}")
    
    # Test health score calculation
    print("\nCalculating health score...")
    health_score = intelligence.get_opportunity_health_score(test_opportunity_id)
    print(f"Health Score: {health_score['health_score']}/100 ({health_score['health_status']})")