"""
AgentSDR Proposal Generation System
AI-powered proposal creation with dynamic templates and personalization
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import openai
from jinja2 import Template, Environment, BaseLoader
from dotenv import load_dotenv
import markdown

load_dotenv()

class ProposalType(Enum):
    STANDARD = "standard"
    CUSTOM = "custom"
    INDUSTRY_SPECIFIC = "industry_specific"
    FOLLOW_UP = "follow_up"
    RFP_RESPONSE = "rfp_response"

class ProposalStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class ProposalSection:
    section_id: str
    title: str
    content: str
    order: int
    is_required: bool = True
    variables: List[str] = None

@dataclass
class ProposalTemplate:
    id: str
    name: str
    description: str
    industry: Optional[str]
    template_type: ProposalType
    sections: List[ProposalSection]
    variables: Dict[str, Any]
    created_by: str
    is_active: bool = True

@dataclass
class ProposalData:
    opportunity_id: str
    client_name: str
    client_company: str
    client_email: str
    client_industry: str
    requirements: Dict[str, Any]
    budget_range: Optional[str]
    timeline: Optional[str]
    decision_makers: List[Dict]
    competitor_info: Optional[Dict]
    custom_variables: Dict[str, Any]

class AgentSDRProposalGenerator:
    """
    AI-powered proposal generation system that creates personalized,
    professional proposals based on client requirements and industry best practices
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.openai_client = None
        
        if os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_client = openai
        
        # Initialize Jinja2 environment for template rendering
        self.template_env = Environment(loader=BaseLoader())
        
        # Load default templates and sections
        self.default_templates = self._initialize_default_templates()
    
    def generate_proposal(self, opportunity_id: str, template_id: Optional[str] = None,
                         custom_requirements: Optional[Dict] = None) -> Optional[str]:
        """
        Generate a complete proposal for an opportunity
        """
        try:
            # Get opportunity and lead data
            opportunity_data = self._get_opportunity_data(opportunity_id)
            if not opportunity_data:
                print("Opportunity not found")
                return None
            
            lead_data = self._get_lead_data(opportunity_data['lead_id'])
            if not lead_data:
                print("Lead data not found")
                return None
            
            # Get or select appropriate template
            if template_id:
                template = self._get_template(template_id)
            else:
                template = self._select_best_template(opportunity_data, lead_data)
            
            if not template:
                print("No suitable template found")
                return None
            
            # Prepare proposal data
            proposal_data = self._prepare_proposal_data(
                opportunity_data, lead_data, custom_requirements
            )
            
            # Generate AI-enhanced content if available
            if self.openai_client:
                enhanced_sections = self._ai_enhance_sections(
                    template.sections, proposal_data
                )
                template.sections = enhanced_sections
            
            # Render proposal content
            proposal_content = self._render_proposal(template, proposal_data)
            
            # Save proposal to database
            proposal_id = self._save_proposal(
                opportunity_id, template.id, proposal_content, 
                opportunity_data['organization_id']
            )
            
            if proposal_id:
                # Generate PDF version
                pdf_path = self._generate_pdf(proposal_id, proposal_content)
                
                # Update proposal with PDF path
                self._update_proposal_pdf_path(proposal_id, pdf_path)
                
                return proposal_id
            
            return None
            
        except Exception as e:
            print(f"Error generating proposal: {e}")
            return None
    
    def create_custom_template(self, organization_id: str, template_data: Dict) -> bool:
        """
        Create a custom proposal template for an organization
        """
        try:
            # Validate template data
            if not self._validate_template_data(template_data):
                return False
            
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Create template sections
            sections = []
            for section_data in template_data.get('sections', []):
                section = ProposalSection(
                    section_id=section_data['id'],
                    title=section_data['title'],
                    content=section_data['content'],
                    order=section_data['order'],
                    is_required=section_data.get('is_required', True),
                    variables=section_data.get('variables', [])
                )
                sections.append(section)
            
            template_record = {
                'name': template_data['name'],
                'description': template_data['description'],
                'industry': template_data.get('industry'),
                'template_type': template_data.get('type', ProposalType.CUSTOM.value),
                'content': {
                    'sections': [
                        {
                            'section_id': s.section_id,
                            'title': s.title,
                            'content': s.content,
                            'order': s.order,
                            'is_required': s.is_required,
                            'variables': s.variables or []
                        }
                        for s in sections
                    ],
                    'variables': template_data.get('variables', {}),
                    'styling': template_data.get('styling', {})
                },
                'organization_id': organization_id,
                'created_by': template_data.get('created_by'),
                'is_active': True
            }
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/proposal_templates",
                headers=headers,
                json=template_record
            )
            
            return response.status_code == 201
            
        except Exception as e:
            print(f"Error creating custom template: {e}")
            return False
    
    def ai_suggest_improvements(self, proposal_id: str) -> List[Dict]:
        """
        Use AI to suggest improvements for an existing proposal
        """
        if not self.openai_client:
            return []
        
        try:
            # Get proposal content
            proposal = self._get_proposal(proposal_id)
            if not proposal:
                return []
            
            # Get associated opportunity and lead data for context
            opportunity = self._get_opportunity_data(proposal['opportunity_id'])
            lead = self._get_lead_data(opportunity['lead_id']) if opportunity else None
            
            if not opportunity or not lead:
                return []
            
            # Prepare context for AI analysis
            context = {
                'client_industry': lead.get('industry', 'Unknown'),
                'client_company': lead.get('company', 'Unknown'),
                'opportunity_stage': opportunity.get('stage', 'Unknown'),
                'opportunity_value': opportunity.get('value', 0),
                'proposal_content': proposal['content']
            }
            
            prompt = f"""
            As a proposal expert, analyze this sales proposal and suggest specific improvements:
            
            Client: {context['client_company']} ({context['client_industry']})
            Opportunity Stage: {context['opportunity_stage']}
            Deal Value: ${context['opportunity_value']:,.2f}
            
            Current Proposal Sections:
            {self._extract_proposal_sections_for_ai(context['proposal_content'])}
            
            Provide 3-5 specific, actionable improvement suggestions focusing on:
            1. Personalization and client-specific value propositions
            2. Competitive differentiation
            3. Clarity and persuasiveness
            4. Call-to-action effectiveness
            5. Industry-specific considerations
            
            Format each suggestion with a clear title and detailed explanation.
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sales proposal consultant with 20+ years of experience."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_suggestions = response.choices[0].message.content.strip()
            
            # Parse AI suggestions into structured format
            suggestions = self._parse_ai_suggestions(ai_suggestions)
            
            return suggestions
            
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return []
    
    def generate_competitive_analysis(self, opportunity_id: str, competitors: List[str]) -> Dict:
        """
        Generate competitive analysis section for proposal
        """
        if not self.openai_client:
            return {}
        
        try:
            # Get opportunity and lead data
            opportunity = self._get_opportunity_data(opportunity_id)
            lead = self._get_lead_data(opportunity['lead_id']) if opportunity else None
            
            if not opportunity or not lead:
                return {}
            
            # Get our company's strengths and offerings
            company_profile = self._get_company_profile(opportunity['organization_id'])
            
            prompt = f"""
            Create a competitive analysis for our proposal to {lead.get('company', 'the client')} 
            in the {lead.get('industry', 'technology')} industry.
            
            Our Company Profile:
            {json.dumps(company_profile, indent=2)}
            
            Main Competitors: {', '.join(competitors)}
            
            Client Requirements:
            {json.dumps(opportunity.get('requirements', {}), indent=2)}
            
            Create a professional competitive analysis that:
            1. Highlights our unique advantages
            2. Addresses potential competitor strengths honestly
            3. Focuses on client value and ROI
            4. Maintains professional tone (no negative competitor bashing)
            5. Includes a comparison matrix if relevant
            
            Format the response as a structured section ready for inclusion in a proposal.
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a strategic sales consultant creating competitive analysis sections."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.8
            )
            
            competitive_analysis = response.choices[0].message.content.strip()
            
            return {
                'title': 'Competitive Analysis',
                'content': competitive_analysis,
                'competitors_analyzed': competitors,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"Error generating competitive analysis: {e}")
            return {}
    
    def personalize_pricing_section(self, opportunity_id: str, base_pricing: Dict) -> Dict:
        """
        Create personalized pricing section based on opportunity data
        """
        try:
            opportunity = self._get_opportunity_data(opportunity_id)
            lead = self._get_lead_data(opportunity['lead_id']) if opportunity else None
            
            if not opportunity or not lead:
                return base_pricing
            
            # Apply industry-specific adjustments
            industry_modifier = self._get_industry_pricing_modifier(lead.get('industry'))
            
            # Apply company size adjustments
            company_size_modifier = self._estimate_company_size_modifier(lead)
            
            # Apply urgency/timeline modifiers
            timeline_modifier = self._get_timeline_modifier(opportunity)
            
            personalized_pricing = base_pricing.copy()
            
            # Apply modifiers to pricing
            for item in personalized_pricing.get('items', []):
                original_price = item.get('price', 0)
                adjusted_price = original_price * industry_modifier * company_size_modifier * timeline_modifier
                item['price'] = round(adjusted_price, 2)
                item['original_price'] = original_price
                item['adjustment_factors'] = {
                    'industry': industry_modifier,
                    'company_size': company_size_modifier,
                    'timeline': timeline_modifier
                }
            
            # Generate pricing rationale if AI is available
            if self.openai_client:
                pricing_rationale = self._generate_pricing_rationale(
                    opportunity, lead, personalized_pricing
                )
                personalized_pricing['rationale'] = pricing_rationale
            
            return personalized_pricing
            
        except Exception as e:
            print(f"Error personalizing pricing: {e}")
            return base_pricing
    
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
    
    def _get_lead_data(self, lead_id: str) -> Optional[Dict]:
        """Get lead data from database"""
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
                return data[0] if data else None
            
            return None
        except Exception as e:
            print(f"Error getting lead data: {e}")
            return None
    
    def _select_best_template(self, opportunity_data: Dict, lead_data: Dict) -> Optional[ProposalTemplate]:
        """Select the best template based on opportunity and lead data"""
        try:
            industry = lead_data.get('industry', '').lower()
            opportunity_stage = opportunity_data.get('stage', '').lower()
            opportunity_value = opportunity_data.get('value', 0)
            
            # Get available templates for the organization
            templates = self._get_organization_templates(opportunity_data['organization_id'])
            
            if not templates:
                # Use default template
                return self._get_default_template()
            
            # Score templates based on relevance
            best_template = None
            best_score = 0
            
            for template in templates:
                score = 0
                
                # Industry match
                if template.get('industry') and template['industry'].lower() == industry:
                    score += 10
                
                # Template type appropriateness
                template_type = template.get('template_type', '')
                if opportunity_stage in ['proposal', 'negotiation'] and template_type == 'standard':
                    score += 5
                elif opportunity_value > 100000 and template_type == 'custom':
                    score += 7
                
                # Usage history and success rate
                template_success_rate = self._get_template_success_rate(template['id'])
                score += template_success_rate * 3
                
                if score > best_score:
                    best_score = score
                    best_template = template
            
            if best_template:
                return self._convert_db_template_to_object(best_template)
            else:
                return self._get_default_template()
                
        except Exception as e:
            print(f"Error selecting template: {e}")
            return self._get_default_template()
    
    def _ai_enhance_sections(self, sections: List[ProposalSection], 
                           proposal_data: ProposalData) -> List[ProposalSection]:
        """Use AI to enhance proposal sections with personalized content"""
        if not self.openai_client:
            return sections
        
        enhanced_sections = []
        
        for section in sections:
            try:
                # Skip if section doesn't need AI enhancement
                if section.section_id in ['cover_page', 'signature', 'appendix']:
                    enhanced_sections.append(section)
                    continue
                
                # Prepare context for AI enhancement
                context = {
                    'client_name': proposal_data.client_name,
                    'client_company': proposal_data.client_company,
                    'client_industry': proposal_data.client_industry,
                    'requirements': proposal_data.requirements,
                    'budget_range': proposal_data.budget_range,
                    'timeline': proposal_data.timeline,
                    'section_title': section.title,
                    'original_content': section.content
                }
                
                prompt = f"""
                Enhance this proposal section for {context['client_company']} in the {context['client_industry']} industry:
                
                Section: {context['section_title']}
                Original Content: {context['original_content']}
                
                Client Requirements:
                {json.dumps(context['requirements'], indent=2)}
                
                Make the content more personalized and compelling while maintaining professionalism.
                Focus on client-specific value propositions and benefits.
                Keep the same structure but enhance language and examples.
                """
                
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert proposal writer specializing in B2B sales content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                
                enhanced_content = response.choices[0].message.content.strip()
                
                # Create enhanced section
                enhanced_section = ProposalSection(
                    section_id=section.section_id,
                    title=section.title,
                    content=enhanced_content,
                    order=section.order,
                    is_required=section.is_required,
                    variables=section.variables
                )
                
                enhanced_sections.append(enhanced_section)
                
            except Exception as e:
                print(f"Error enhancing section {section.section_id}: {e}")
                # Fall back to original section
                enhanced_sections.append(section)
        
        return enhanced_sections
    
    def _render_proposal(self, template: ProposalTemplate, proposal_data: ProposalData) -> Dict:
        """Render proposal using template and data"""
        try:
            # Prepare template variables
            template_vars = {
                'client_name': proposal_data.client_name,
                'client_company': proposal_data.client_company,
                'client_email': proposal_data.client_email,
                'client_industry': proposal_data.client_industry,
                'today_date': datetime.now().strftime('%B %d, %Y'),
                'proposal_id': f"PROP-{int(datetime.now().timestamp())}",
                'requirements': proposal_data.requirements,
                'budget_range': proposal_data.budget_range,
                'timeline': proposal_data.timeline,
                'decision_makers': proposal_data.decision_makers,
                **proposal_data.custom_variables
            }
            
            # Render each section
            rendered_sections = []
            
            for section in sorted(template.sections, key=lambda x: x.order):
                try:
                    # Render section content with Jinja2
                    section_template = self.template_env.from_string(section.content)
                    rendered_content = section_template.render(**template_vars)
                    
                    rendered_sections.append({
                        'section_id': section.section_id,
                        'title': section.title,
                        'content': rendered_content,
                        'order': section.order
                    })
                    
                except Exception as e:
                    print(f"Error rendering section {section.section_id}: {e}")
                    # Use original content as fallback
                    rendered_sections.append({
                        'section_id': section.section_id,
                        'title': section.title,
                        'content': section.content,
                        'order': section.order
                    })
            
            return {
                'template_id': template.id,
                'sections': rendered_sections,
                'metadata': {
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'template_name': template.name,
                    'client_company': proposal_data.client_company,
                    'proposal_type': template.template_type.value
                }
            }
            
        except Exception as e:
            print(f"Error rendering proposal: {e}")
            return {}
    
    def _save_proposal(self, opportunity_id: str, template_id: str, 
                      content: Dict, organization_id: str) -> Optional[str]:
        """Save proposal to database"""
        try:
            headers = {
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': 'application/json'
            }
            
            proposal_data = {
                'title': f"Proposal for {content['metadata']['client_company']}",
                'opportunity_id': opportunity_id,
                'template_id': template_id,
                'organization_id': organization_id,
                'created_by': None,  # Would be set based on current user
                'status': ProposalStatus.DRAFT.value,
                'content': content,
                'total_value': 0,  # Would be calculated from pricing sections
                'expiry_date': (datetime.now() + timedelta(days=30)).date().isoformat()
            }
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/proposals",
                headers=headers,
                json=proposal_data
            )
            
            if response.status_code == 201:
                created_proposal = response.json()
                return created_proposal[0]['id'] if created_proposal else None
            else:
                print(f"Error saving proposal: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error saving proposal: {e}")
            return None
    
    def _initialize_default_templates(self) -> Dict[str, ProposalTemplate]:
        """Initialize default proposal templates"""
        return {
            'standard_saas': ProposalTemplate(
                id='default_saas',
                name='Standard SaaS Proposal',
                description='Standard template for SaaS products',
                industry='technology',
                template_type=ProposalType.STANDARD,
                sections=[
                    ProposalSection(
                        section_id='executive_summary',
                        title='Executive Summary',
                        content="""
                        Dear {{ client_name }},
                        
                        Thank you for considering our solution for {{ client_company }}. 
                        This proposal outlines how our platform can address your specific needs 
                        in the {{ client_industry }} industry and deliver measurable results.
                        
                        Key Benefits:
                        • Increased efficiency and productivity
                        • Cost reduction through automation
                        • Scalable solution that grows with your business
                        • Comprehensive support and training
                        """,
                        order=1
                    ),
                    ProposalSection(
                        section_id='solution_overview',
                        title='Solution Overview',
                        content="""
                        Our platform is specifically designed to meet the challenges 
                        faced by companies like {{ client_company }} in the {{ client_industry }} sector.
                        
                        Based on your requirements, we recommend:
                        {% for req in requirements %}
                        • {{ req }}
                        {% endfor %}
                        """,
                        order=2
                    ),
                    ProposalSection(
                        section_id='implementation',
                        title='Implementation Plan',
                        content="""
                        We propose a phased implementation approach:
                        
                        Phase 1: Setup and Configuration (Weeks 1-2)
                        Phase 2: Data Migration and Testing (Weeks 3-4)
                        Phase 3: Training and Go-Live (Week 5)
                        Phase 4: Optimization and Support (Ongoing)
                        
                        Timeline: {{ timeline or '4-6 weeks' }}
                        """,
                        order=3
                    )
                ],
                variables={},
                created_by='system',
                is_active=True
            )
        }
    
    # Additional helper methods would be implemented here...
    # Including PDF generation, email sending, tracking, etc.

# Example usage and testing
if __name__ == "__main__":
    generator = AgentSDRProposalGenerator()
    
    # Test proposal generation
    test_opportunity_id = "test-opp-123"
    
    print("Generating proposal...")
    proposal_id = generator.generate_proposal(test_opportunity_id)
    
    if proposal_id:
        print(f"Proposal generated successfully: {proposal_id}")
        
        # Test AI suggestions
        print("Getting AI improvement suggestions...")
        suggestions = generator.ai_suggest_improvements(proposal_id)
        
        for suggestion in suggestions:
            print(f"- {suggestion.get('title', 'Suggestion')}: {suggestion.get('description', '')}")
    else:
        print("Failed to generate proposal")