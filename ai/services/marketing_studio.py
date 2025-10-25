"""
🎨 ChatterFix CMMS - AI-Driven Marketing Studio
Automated content creation, social media management, and thought leadership

Features:
- Automated social media content generation and publishing
- Case study creation from customer success metrics
- Press release templates and distribution
- Thought leadership content for LinkedIn/Medium/Twitter
- Marketing performance analytics and attribution tracking
- Brand voice consistency and content optimization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import re

import openai
import anthropic
import aioredis
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentType(Enum):
    SOCIAL_MEDIA = "social_media"
    CASE_STUDY = "case_study"
    PRESS_RELEASE = "press_release"
    THOUGHT_LEADERSHIP = "thought_leadership"
    PRODUCT_ANNOUNCEMENT = "product_announcement"
    CUSTOMER_SUCCESS = "customer_success"

class Platform(Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    MEDIUM = "medium"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    COMPANY_BLOG = "company_blog"

class ContentStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"

@dataclass
class ContentRequest:
    content_type: ContentType
    platform: Platform
    topic: str
    target_audience: str
    tone: str  # professional, casual, technical, inspirational
    include_metrics: bool = False
    customer_reference: Optional[str] = None
    publish_immediately: bool = False
    scheduled_time: Optional[datetime] = None

@dataclass
class GeneratedContent:
    content_id: str
    content_type: ContentType
    platform: Platform
    title: str
    body: str
    hashtags: List[str]
    mentions: List[str]
    image_prompt: Optional[str]
    cta: str
    metadata: Dict
    status: ContentStatus
    created_at: datetime
    scheduled_for: Optional[datetime]

class MarketingStudio:
    """AI-powered marketing content generation and distribution platform"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI()
        self.anthropic_client = anthropic.AsyncAnthropic()
        self.redis_client = None
        
        self.db_config = {
            'host': 'localhost',
            'database': 'chatterfix_cmms',
            'user': 'postgres',
            'password': 'your_password'
        }
        
        # Brand voice guidelines
        self.brand_voice = {
            'tone': 'Professional yet approachable',
            'personality': 'Innovative, reliable, customer-focused',
            'values': ['Innovation', 'Reliability', 'Customer Success', 'Efficiency'],
            'messaging_pillars': [
                'AI-powered maintenance management',
                'Predictive analytics and prevention',
                'User-friendly mobile experience',
                'Measurable ROI and cost savings',
                'Enterprise-grade security and reliability'
            ]
        }
        
        # Content templates by platform
        self.platform_templates = self._load_platform_templates()
        
        # Industry hashtags and keywords
        self.industry_hashtags = {
            'cmms': ['#CMMS', '#MaintenanceManagement', '#PredictiveMaintenance'],
            'manufacturing': ['#Manufacturing', '#Industry40', '#SmartFactory'],
            'healthcare': ['#HealthTech', '#BiomedicalEngineering', '#HealthcareIT'],
            'energy': ['#EnergyManagement', '#UtilityManagement', '#RenewableEnergy'],
            'ai': ['#ArtificialIntelligence', '#MachineLearning', '#AI', '#TechInnovation']
        }
        
    async def initialize_redis(self):
        """Initialize Redis connection for content caching"""
        try:
            self.redis_client = await aioredis.from_url("redis://localhost")
            logger.info("Redis connection established for marketing studio")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    def _load_platform_templates(self) -> Dict[Platform, Dict]:
        """Load platform-specific content templates and constraints"""
        return {
            Platform.LINKEDIN: {
                'max_length': 3000,
                'optimal_length': 150,
                'hashtag_limit': 5,
                'best_times': ['09:00', '12:00', '17:00'],
                'content_style': 'Professional insights and industry expertise',
                'cta_examples': ['Learn more:', 'Share your thoughts:', 'Connect with us:']
            },
            Platform.TWITTER: {
                'max_length': 280,
                'optimal_length': 120,
                'hashtag_limit': 3,
                'best_times': ['08:00', '13:00', '18:00'],
                'content_style': 'Quick insights and industry news',
                'cta_examples': ['Read more:', 'Thoughts?', 'Join the conversation:']
            },
            Platform.MEDIUM: {
                'max_length': 10000,
                'optimal_length': 1200,
                'hashtag_limit': 10,
                'best_times': ['10:00', '14:00', '19:00'],
                'content_style': 'In-depth thought leadership and analysis',
                'cta_examples': ['Discover more:', 'Share your experience:', 'Connect:']
            },
            Platform.COMPANY_BLOG: {
                'max_length': 5000,
                'optimal_length': 800,
                'hashtag_limit': 8,
                'best_times': ['10:00', '14:00'],
                'content_style': 'Educational and value-driven content',
                'cta_examples': ['Learn more about ChatterFix:', 'Schedule a demo:', 'Contact us:']
            }
        }
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate content based on request specifications"""
        try:
            content_id = hashlib.md5(f"{request.content_type.value}{request.platform.value}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            
            # Get platform constraints
            platform_config = self.platform_templates.get(request.platform, {})
            
            # Generate content based on type
            if request.content_type == ContentType.CASE_STUDY:
                content = await self._generate_case_study(request, platform_config)
            elif request.content_type == ContentType.PRESS_RELEASE:
                content = await self._generate_press_release(request, platform_config)
            elif request.content_type == ContentType.THOUGHT_LEADERSHIP:
                content = await self._generate_thought_leadership(request, platform_config)
            elif request.content_type == ContentType.SOCIAL_MEDIA:
                content = await self._generate_social_media_post(request, platform_config)
            elif request.content_type == ContentType.CUSTOMER_SUCCESS:
                content = await self._generate_customer_success_story(request, platform_config)
            else:
                content = await self._generate_general_content(request, platform_config)
            
            # Generate hashtags and mentions
            hashtags = await self._generate_hashtags(request.topic, request.platform)
            mentions = await self._generate_mentions(request.topic, request.platform)
            
            # Generate image prompt if needed
            image_prompt = await self._generate_image_prompt(content['title'], content['body'])
            
            # Create content object
            generated_content = GeneratedContent(
                content_id=content_id,
                content_type=request.content_type,
                platform=request.platform,
                title=content['title'],
                body=content['body'],
                hashtags=hashtags,
                mentions=mentions,
                image_prompt=image_prompt,
                cta=content['cta'],
                metadata={
                    'topic': request.topic,
                    'audience': request.target_audience,
                    'tone': request.tone,
                    'word_count': len(content['body'].split()),
                    'character_count': len(content['body']),
                    'generation_model': content.get('model', 'gpt-4'),
                    'brand_voice_score': await self._calculate_brand_voice_score(content['body'])
                },
                status=ContentStatus.DRAFT,
                created_at=datetime.now(),
                scheduled_for=request.scheduled_time
            )
            
            # Save to database
            await self._save_content_to_db(generated_content)
            
            # Cache for quick access
            if self.redis_client:
                cache_key = f"content:{content_id}"
                await self.redis_client.setex(
                    cache_key, 
                    86400,  # 24 hours
                    json.dumps(generated_content.__dict__, default=str)
                )
            
            return generated_content
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate content")
    
    async def _generate_case_study(self, request: ContentRequest, platform_config: Dict) -> Dict:
        """Generate customer case study content"""
        try:
            # Get customer metrics if reference provided
            customer_data = ""
            if request.customer_reference:
                customer_data = await self._get_customer_metrics(request.customer_reference)
            
            prompt = f"""
            Write a compelling case study for ChatterFix CMMS focusing on {request.topic}.
            
            Brand Voice: {self.brand_voice['tone']}
            Target Audience: {request.target_audience}
            Content Tone: {request.tone}
            Platform: {request.platform.value}
            Max Length: {platform_config.get('optimal_length', 800)} words
            
            {customer_data}
            
            Structure:
            1. Compelling headline
            2. Challenge/Problem statement
            3. Solution implementation
            4. Measurable results and ROI
            5. Customer quote (if data available)
            6. Call-to-action
            
            Focus on measurable business outcomes, specific metrics, and clear value proposition.
            Include relevant industry context and competitive advantages.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Extract title and body
            lines = content.split('\n')
            title = lines[0].strip().replace('#', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            # Generate CTA
            cta_examples = platform_config.get('cta_examples', ['Learn more:'])
            cta = f"{cta_examples[0]} Schedule a ChatterFix demo to see similar results"
            
            return {
                'title': title,
                'body': body,
                'cta': cta,
                'model': 'gpt-4'
            }
            
        except Exception as e:
            logger.error(f"Error generating case study: {e}")
            raise
    
    async def _generate_press_release(self, request: ContentRequest, platform_config: Dict) -> Dict:
        """Generate press release content"""
        try:
            prompt = f"""
            Write a professional press release for ChatterFix CMMS about {request.topic}.
            
            Brand Voice: {self.brand_voice['tone']}
            Company Values: {', '.join(self.brand_voice['values'])}
            Target Audience: {request.target_audience}
            Content Tone: {request.tone}
            
            Standard press release format:
            1. Compelling headline
            2. Dateline and lead paragraph with who, what, when, where, why
            3. Quote from company executive
            4. Supporting details and context
            5. Company boilerplate
            6. Contact information placeholder
            
            Focus on newsworthy angles, industry impact, and customer benefits.
            Include relevant market data and competitive positioning.
            """
            
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Extract title and body
            lines = content.split('\n')
            title = lines[0].strip()
            body = '\n'.join(lines[1:]).strip()
            
            cta = "For more information about ChatterFix CMMS, visit chatterfix.com"
            
            return {
                'title': title,
                'body': body,
                'cta': cta,
                'model': 'claude-3-sonnet'
            }
            
        except Exception as e:
            logger.error(f"Error generating press release: {e}")
            raise
    
    async def _generate_thought_leadership(self, request: ContentRequest, platform_config: Dict) -> Dict:
        """Generate thought leadership content"""
        try:
            prompt = f"""
            Write an insightful thought leadership article about {request.topic} in the CMMS/maintenance management industry.
            
            Brand Voice: {self.brand_voice['personality']}
            Messaging Pillars: {', '.join(self.brand_voice['messaging_pillars'])}
            Target Audience: {request.target_audience}
            Content Tone: {request.tone}
            Platform: {request.platform.value}
            Target Length: {platform_config.get('optimal_length', 1000)} words
            
            Structure:
            1. Attention-grabbing headline
            2. Hook with industry trend or insight
            3. Expert analysis and perspective
            4. Real-world examples and data
            5. Future predictions and recommendations
            6. Call-to-action for engagement
            
            Position ChatterFix as an industry thought leader with deep expertise.
            Include forward-thinking insights and actionable recommendations.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            
            # Extract title and body
            lines = content.split('\n')
            title = lines[0].strip().replace('#', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            cta = "What's your experience with AI in maintenance? Share your thoughts below."
            
            return {
                'title': title,
                'body': body,
                'cta': cta,
                'model': 'gpt-4'
            }
            
        except Exception as e:
            logger.error(f"Error generating thought leadership: {e}")
            raise
    
    async def _generate_social_media_post(self, request: ContentRequest, platform_config: Dict) -> Dict:
        """Generate social media post content"""
        try:
            max_length = platform_config.get('max_length', 280)
            optimal_length = platform_config.get('optimal_length', 150)
            
            prompt = f"""
            Create an engaging social media post for {request.platform.value} about {request.topic}.
            
            Brand Voice: {self.brand_voice['tone']}
            Target Audience: {request.target_audience}
            Content Tone: {request.tone}
            Maximum Length: {max_length} characters
            Optimal Length: {optimal_length} characters
            
            Requirements:
            - Engaging hook in first 50 characters
            - Clear value proposition
            - Include question or engagement prompt
            - Professional but conversational tone
            - Platform-appropriate formatting
            
            Focus on driving engagement, shares, and comments.
            Make it platform-native and shareable.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.9
            )
            
            content = response.choices[0].message.content.strip()
            
            # Ensure content fits platform constraints
            if len(content) > max_length:
                content = content[:max_length-3] + "..."
            
            title = f"{request.platform.value.title()} Post - {request.topic}"
            cta = "Share your thoughts in the comments!"
            
            return {
                'title': title,
                'body': content,
                'cta': cta,
                'model': 'gpt-4'
            }
            
        except Exception as e:
            logger.error(f"Error generating social media post: {e}")
            raise
    
    async def _generate_customer_success_story(self, request: ContentRequest, platform_config: Dict) -> Dict:
        """Generate customer success story content"""
        try:
            # Get real customer metrics
            customer_data = ""
            if request.customer_reference:
                customer_data = await self._get_customer_metrics(request.customer_reference)
            
            prompt = f"""
            Create an inspiring customer success story for ChatterFix CMMS about {request.topic}.
            
            Brand Voice: {self.brand_voice['personality']}
            Target Audience: {request.target_audience}
            Content Tone: {request.tone}
            Platform: {request.platform.value}
            
            {customer_data}
            
            Story Structure:
            1. Compelling headline with result/benefit
            2. Customer background and challenge
            3. Solution journey with ChatterFix
            4. Specific results and metrics
            5. Customer testimonial quote
            6. Call-to-action for similar companies
            
            Focus on transformation story with concrete business outcomes.
            Make it relatable and inspiring for similar companies.
            """
            
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Extract title and body
            lines = content.split('\n')
            title = lines[0].strip()
            body = '\n'.join(lines[1:]).strip()
            
            cta = "Ready for similar results? Discover ChatterFix CMMS"
            
            return {
                'title': title,
                'body': body,
                'cta': cta,
                'model': 'claude-3-sonnet'
            }
            
        except Exception as e:
            logger.error(f"Error generating customer success story: {e}")
            raise
    
    async def _generate_general_content(self, request: ContentRequest, platform_config: Dict) -> Dict:
        """Generate general content for any topic"""
        try:
            optimal_length = platform_config.get('optimal_length', 500)
            
            prompt = f"""
            Create engaging content about {request.topic} for ChatterFix CMMS.
            
            Brand Voice: {self.brand_voice['tone']}
            Company Values: {', '.join(self.brand_voice['values'])}
            Target Audience: {request.target_audience}
            Content Tone: {request.tone}
            Platform: {request.platform.value}
            Target Length: {optimal_length} words
            
            Content should:
            - Provide value to the target audience
            - Position ChatterFix as an industry expert
            - Include actionable insights or tips
            - End with engaging call-to-action
            
            Make it informative, engaging, and brand-aligned.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            
            # Extract title and body
            lines = content.split('\n')
            title = lines[0].strip().replace('#', '').strip()
            body = '\n'.join(lines[1:]).strip()
            
            cta = "Learn more about ChatterFix CMMS"
            
            return {
                'title': title,
                'body': body,
                'cta': cta,
                'model': 'gpt-4'
            }
            
        except Exception as e:
            logger.error(f"Error generating general content: {e}")
            raise
    
    async def _get_customer_metrics(self, customer_id: str) -> str:
        """Get customer metrics for case study content"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT 
                    c.company_name, c.industry_vertical, c.company_size,
                    r.total_cost_savings, r.roi_percentage, r.payback_period_months,
                    r.downtime_reduction_percent, r.efficiency_improvement_percent
                FROM customers c
                LEFT JOIN customer_roi_summary r ON c.id = r.customer_id
                WHERE c.id = %s
            """, (customer_id,))
            
            data = cur.fetchone()
            conn.close()
            
            if data:
                return f"""
                Customer Context:
                - Company: {data['company_name']} ({data['industry_vertical']})
                - Size: {data['company_size']} employees
                - ROI Achieved: {data['roi_percentage']}%
                - Cost Savings: ${data['total_cost_savings']:,}
                - Payback Period: {data['payback_period_months']} months
                - Downtime Reduction: {data['downtime_reduction_percent']}%
                - Efficiency Improvement: {data['efficiency_improvement_percent']}%
                """
            else:
                return "No customer metrics available."
                
        except Exception as e:
            logger.error(f"Error getting customer metrics: {e}")
            return ""
    
    async def _generate_hashtags(self, topic: str, platform: Platform) -> List[str]:
        """Generate relevant hashtags for content"""
        try:
            platform_config = self.platform_templates.get(platform, {})
            max_hashtags = platform_config.get('hashtag_limit', 5)
            
            # Base CMMS hashtags
            hashtags = list(self.industry_hashtags['cmms'])
            
            # Add topic-specific hashtags
            topic_lower = topic.lower()
            if 'manufacturing' in topic_lower or 'factory' in topic_lower:
                hashtags.extend(self.industry_hashtags['manufacturing'])
            elif 'healthcare' in topic_lower or 'hospital' in topic_lower:
                hashtags.extend(self.industry_hashtags['healthcare'])
            elif 'energy' in topic_lower or 'utility' in topic_lower:
                hashtags.extend(self.industry_hashtags['energy'])
            
            # Add AI hashtags if relevant
            if any(word in topic_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'predictive']):
                hashtags.extend(self.industry_hashtags['ai'])
            
            # Remove duplicates and limit
            unique_hashtags = list(dict.fromkeys(hashtags))
            return unique_hashtags[:max_hashtags]
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return ['#CMMS', '#MaintenanceManagement']
    
    async def _generate_mentions(self, topic: str, platform: Platform) -> List[str]:
        """Generate relevant mentions for content"""
        mentions = []
        
        # Platform-specific mentions
        if platform == Platform.LINKEDIN:
            mentions = ['@ChatterFix-CMMS']
        elif platform == Platform.TWITTER:
            mentions = ['@ChatterFixCMMS']
        
        # Add industry influencer mentions if relevant
        topic_lower = topic.lower()
        if 'manufacturing' in topic_lower:
            mentions.extend(['@ManufacturingNet', '@IndustryWeek'])
        elif 'healthcare' in topic_lower:
            mentions.extend(['@HealthTechMag', '@HealthcareIT'])
        
        return mentions
    
    async def _generate_image_prompt(self, title: str, body: str) -> str:
        """Generate image prompt for visual content creation"""
        try:
            prompt = f"""
            Create a visual image prompt for this content:
            Title: {title}
            Content: {body[:200]}...
            
            Generate a professional image description for:
            - Modern, clean design
            - Technology/AI theme
            - Industrial/maintenance context
            - ChatterFix brand colors (blue, white, gray)
            - Professional stock photo style
            
            Provide only the image description, no explanations.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating image prompt: {e}")
            return "Professional maintenance technology interface with modern design"
    
    async def _calculate_brand_voice_score(self, content: str) -> float:
        """Calculate how well content matches brand voice guidelines"""
        try:
            # Check for brand values and messaging
            score = 0.0
            content_lower = content.lower()
            
            # Check for value keywords
            value_keywords = ['innovation', 'reliable', 'customer', 'efficient', 'predictive', 'ai']
            value_matches = sum(1 for keyword in value_keywords if keyword in content_lower)
            score += (value_matches / len(value_keywords)) * 30
            
            # Check for messaging pillars
            pillar_keywords = ['ai-powered', 'predictive', 'mobile', 'roi', 'security', 'analytics']
            pillar_matches = sum(1 for keyword in pillar_keywords if keyword in content_lower)
            score += (pillar_matches / len(pillar_keywords)) * 30
            
            # Check tone indicators
            professional_indicators = ['solution', 'optimization', 'efficiency', 'results', 'performance']
            professional_matches = sum(1 for indicator in professional_indicators if indicator in content_lower)
            score += (professional_matches / len(professional_indicators)) * 40
            
            return min(100.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating brand voice score: {e}")
            return 50.0
    
    async def _save_content_to_db(self, content: GeneratedContent):
        """Save generated content to database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO marketing_content 
                (content_id, content_type, platform, title, body, hashtags, mentions, 
                 image_prompt, cta, metadata, status, created_at, scheduled_for)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                content.content_id,
                content.content_type.value,
                content.platform.value,
                content.title,
                content.body,
                json.dumps(content.hashtags),
                json.dumps(content.mentions),
                content.image_prompt,
                content.cta,
                json.dumps(content.metadata),
                content.status.value,
                content.created_at,
                content.scheduled_for
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Content {content.content_id} saved to database")
            
        except Exception as e:
            logger.error(f"Error saving content to database: {e}")
    
    async def publish_content(self, content_id: str, platform: Platform) -> Dict:
        """Publish content to specified platform"""
        try:
            # Get content from database
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM marketing_content WHERE content_id = %s
            """, (content_id,))
            
            content_data = cur.fetchone()
            conn.close()
            
            if not content_data:
                raise HTTPException(status_code=404, detail="Content not found")
            
            # Platform-specific publishing logic
            result = {}
            if platform == Platform.LINKEDIN:
                result = await self._publish_to_linkedin(content_data)
            elif platform == Platform.TWITTER:
                result = await self._publish_to_twitter(content_data)
            elif platform == Platform.MEDIUM:
                result = await self._publish_to_medium(content_data)
            elif platform == Platform.COMPANY_BLOG:
                result = await self._publish_to_blog(content_data)
            else:
                result = {'status': 'simulated', 'message': f'Publishing simulated for {platform.value}'}
            
            # Update content status
            await self._update_content_status(content_id, ContentStatus.PUBLISHED)
            
            # Log publication
            await self._log_publication_metrics(content_id, platform, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error publishing content: {e}")
            raise HTTPException(status_code=500, detail="Failed to publish content")
    
    async def _publish_to_linkedin(self, content_data: Dict) -> Dict:
        """Publish content to LinkedIn (simulation - requires API credentials)"""
        try:
            # This would integrate with LinkedIn API
            # For now, return simulation result
            
            post_text = f"{content_data['title']}\n\n{content_data['body']}\n\n{content_data['cta']}"
            hashtags = json.loads(content_data['hashtags'])
            post_text += f"\n\n{' '.join(hashtags)}"
            
            # Simulate API call
            await asyncio.sleep(0.5)  # Simulate network delay
            
            return {
                'platform': 'linkedin',
                'status': 'published',
                'post_id': f"linkedin_{content_data['content_id']}",
                'url': f"https://linkedin.com/posts/{content_data['content_id']}",
                'published_at': datetime.now().isoformat(),
                'character_count': len(post_text)
            }
            
        except Exception as e:
            logger.error(f"Error publishing to LinkedIn: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _publish_to_twitter(self, content_data: Dict) -> Dict:
        """Publish content to Twitter (simulation - requires API credentials)"""
        try:
            # This would integrate with Twitter API v2
            # For now, return simulation result
            
            post_text = content_data['body']
            hashtags = json.loads(content_data['hashtags'])
            mentions = json.loads(content_data['mentions'])
            
            # Add hashtags and mentions
            post_text += f"\n\n{' '.join(hashtags)} {' '.join(mentions)}"
            
            # Ensure under 280 characters
            if len(post_text) > 280:
                post_text = post_text[:277] + "..."
            
            # Simulate API call
            await asyncio.sleep(0.3)
            
            return {
                'platform': 'twitter',
                'status': 'published',
                'tweet_id': f"twitter_{content_data['content_id']}",
                'url': f"https://twitter.com/ChatterFixCMMS/status/{content_data['content_id']}",
                'published_at': datetime.now().isoformat(),
                'character_count': len(post_text)
            }
            
        except Exception as e:
            logger.error(f"Error publishing to Twitter: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _publish_to_medium(self, content_data: Dict) -> Dict:
        """Publish content to Medium (simulation)"""
        try:
            # This would integrate with Medium API
            # For now, return simulation result
            
            await asyncio.sleep(1.0)  # Simulate processing time
            
            return {
                'platform': 'medium',
                'status': 'published',
                'post_id': f"medium_{content_data['content_id']}",
                'url': f"https://medium.com/@chatterfix/{content_data['content_id']}",
                'published_at': datetime.now().isoformat(),
                'word_count': len(content_data['body'].split())
            }
            
        except Exception as e:
            logger.error(f"Error publishing to Medium: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _publish_to_blog(self, content_data: Dict) -> Dict:
        """Publish content to company blog"""
        try:
            # This would integrate with company CMS
            # For now, return simulation result
            
            await asyncio.sleep(0.8)
            
            return {
                'platform': 'company_blog',
                'status': 'published',
                'post_id': f"blog_{content_data['content_id']}",
                'url': f"https://chatterfix.com/blog/{content_data['content_id']}",
                'published_at': datetime.now().isoformat(),
                'seo_score': 85
            }
            
        except Exception as e:
            logger.error(f"Error publishing to blog: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _update_content_status(self, content_id: str, status: ContentStatus):
        """Update content status in database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE marketing_content 
                SET status = %s, updated_at = %s
                WHERE content_id = %s
            """, (status.value, datetime.now(), content_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating content status: {e}")
    
    async def _log_publication_metrics(self, content_id: str, platform: Platform, result: Dict):
        """Log publication metrics for analytics"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO content_publications 
                (content_id, platform, publication_result, published_at)
                VALUES (%s, %s, %s, %s)
            """, (
                content_id,
                platform.value,
                json.dumps(result),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Publication metrics logged for {content_id} on {platform.value}")
            
        except Exception as e:
            logger.error(f"Error logging publication metrics: {e}")
    
    async def get_content_performance(self, content_id: str) -> Dict:
        """Get performance analytics for published content"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get content details
            cur.execute("""
                SELECT mc.*, cp.publication_result, cp.published_at as publication_date
                FROM marketing_content mc
                LEFT JOIN content_publications cp ON mc.content_id = cp.content_id
                WHERE mc.content_id = %s
            """, (content_id,))
            
            content_data = cur.fetchone()
            
            # Get engagement metrics (simulated for demo)
            cur.execute("""
                SELECT 
                    SUM(likes) as total_likes,
                    SUM(shares) as total_shares,
                    SUM(comments) as total_comments,
                    SUM(clicks) as total_clicks,
                    SUM(impressions) as total_impressions
                FROM content_engagement_metrics 
                WHERE content_id = %s
            """, (content_id,))
            
            engagement_data = cur.fetchone()
            conn.close()
            
            if not content_data:
                raise HTTPException(status_code=404, detail="Content not found")
            
            # Calculate engagement rate
            total_engagement = (
                (engagement_data['total_likes'] or 0) +
                (engagement_data['total_shares'] or 0) +
                (engagement_data['total_comments'] or 0)
            )
            
            engagement_rate = 0
            if engagement_data['total_impressions']:
                engagement_rate = (total_engagement / engagement_data['total_impressions']) * 100
            
            return {
                'content_id': content_id,
                'title': content_data['title'],
                'platform': content_data['platform'],
                'status': content_data['status'],
                'created_at': content_data['created_at'].isoformat(),
                'published_at': content_data['publication_date'].isoformat() if content_data['publication_date'] else None,
                'performance_metrics': {
                    'impressions': engagement_data['total_impressions'] or 0,
                    'likes': engagement_data['total_likes'] or 0,
                    'shares': engagement_data['total_shares'] or 0,
                    'comments': engagement_data['total_comments'] or 0,
                    'clicks': engagement_data['total_clicks'] or 0,
                    'engagement_rate': round(engagement_rate, 2)
                },
                'content_metrics': json.loads(content_data['metadata']) if content_data['metadata'] else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting content performance: {e}")
            raise HTTPException(status_code=500, detail="Failed to get content performance")
    
    async def schedule_content_calendar(self, days_ahead: int = 30) -> Dict:
        """Generate content calendar with automated posting schedule"""
        try:
            # Content themes by day of week
            weekly_themes = {
                0: "Monday Motivation - Industry insights and trends",
                1: "Technical Tuesday - Product features and capabilities",
                2: "Wisdom Wednesday - Best practices and tips",
                3: "Throwback Thursday - Customer success stories",
                4: "Feature Friday - New announcements and updates",
                5: "Saturday Spotlight - Thought leadership",
                6: "Sunday Summary - Week recap and preview"
            }
            
            # Generate content calendar
            calendar = []
            start_date = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
            
            for day in range(days_ahead):
                post_date = start_date + timedelta(days=day)
                day_of_week = post_date.weekday()
                theme = weekly_themes[day_of_week]
                
                # Different content types by platform rotation
                platforms = [Platform.LINKEDIN, Platform.TWITTER, Platform.COMPANY_BLOG]
                platform = platforms[day % len(platforms)]
                
                # Generate content topic based on theme
                if "motivation" in theme.lower():
                    topic = "AI trends in predictive maintenance"
                    content_type = ContentType.THOUGHT_LEADERSHIP
                elif "technical" in theme.lower():
                    topic = "ChatterFix mobile app features"
                    content_type = ContentType.SOCIAL_MEDIA
                elif "wisdom" in theme.lower():
                    topic = "Maintenance best practices"
                    content_type = ContentType.THOUGHT_LEADERSHIP
                elif "throwback" in theme.lower():
                    topic = "Customer ROI success story"
                    content_type = ContentType.CUSTOMER_SUCCESS
                elif "feature" in theme.lower():
                    topic = "New ChatterFix AI capabilities"
                    content_type = ContentType.PRODUCT_ANNOUNCEMENT
                else:
                    topic = "Industry insights and analysis"
                    content_type = ContentType.THOUGHT_LEADERSHIP
                
                calendar_entry = {
                    'date': post_date.isoformat(),
                    'day_of_week': post_date.strftime('%A'),
                    'theme': theme,
                    'platform': platform.value,
                    'content_type': content_type.value,
                    'topic': topic,
                    'optimal_time': self.platform_templates[platform]['best_times'][0],
                    'status': 'scheduled'
                }
                
                calendar.append(calendar_entry)
            
            # Save calendar to database
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            for entry in calendar:
                cur.execute("""
                    INSERT INTO content_calendar 
                    (scheduled_date, platform, content_type, topic, theme, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (scheduled_date, platform) DO UPDATE SET
                    content_type = EXCLUDED.content_type,
                    topic = EXCLUDED.topic,
                    theme = EXCLUDED.theme,
                    updated_at = %s
                """, (
                    datetime.fromisoformat(entry['date']),
                    entry['platform'],
                    entry['content_type'],
                    entry['topic'],
                    entry['theme'],
                    entry['status'],
                    datetime.now(),
                    datetime.now()
                ))
            
            conn.commit()
            conn.close()
            
            return {
                'calendar_generated': True,
                'days_scheduled': days_ahead,
                'total_posts': len(calendar),
                'platforms_covered': list(set(entry['platform'] for entry in calendar)),
                'content_types': list(set(entry['content_type'] for entry in calendar)),
                'calendar': calendar
            }
            
        except Exception as e:
            logger.error(f"Error generating content calendar: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate content calendar")

# FastAPI application for marketing studio
app = FastAPI(title="ChatterFix Marketing Studio", version="2.0.0")
studio = MarketingStudio()

@app.on_event("startup")
async def startup_event():
    await studio.initialize_redis()

@app.post("/api/marketing/content/generate")
async def generate_content(request_data: Dict):
    """Generate content based on specifications"""
    try:
        request = ContentRequest(
            content_type=ContentType(request_data['content_type']),
            platform=Platform(request_data['platform']),
            topic=request_data['topic'],
            target_audience=request_data['target_audience'],
            tone=request_data['tone'],
            include_metrics=request_data.get('include_metrics', False),
            customer_reference=request_data.get('customer_reference'),
            publish_immediately=request_data.get('publish_immediately', False),
            scheduled_time=datetime.fromisoformat(request_data['scheduled_time']) if request_data.get('scheduled_time') else None
        )
        
        content = await studio.generate_content(request)
        
        return {
            'content_id': content.content_id,
            'title': content.title,
            'body': content.body,
            'hashtags': content.hashtags,
            'mentions': content.mentions,
            'cta': content.cta,
            'metadata': content.metadata,
            'status': content.status.value,
            'created_at': content.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in generate content endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/marketing/content/{content_id}/publish/{platform}")
async def publish_content(content_id: str, platform: str):
    """Publish content to specified platform"""
    platform_enum = Platform(platform)
    result = await studio.publish_content(content_id, platform_enum)
    return result

@app.get("/api/marketing/content/{content_id}/performance")
async def get_content_performance(content_id: str):
    """Get content performance metrics"""
    performance = await studio.get_content_performance(content_id)
    return performance

@app.post("/api/marketing/calendar/generate")
async def generate_content_calendar(days_ahead: int = 30):
    """Generate automated content calendar"""
    calendar = await studio.schedule_content_calendar(days_ahead)
    return calendar

@app.get("/api/marketing/dashboard")
async def get_marketing_dashboard():
    """Get marketing performance dashboard"""
    try:
        conn = psycopg2.connect(**studio.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get content statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total_content,
                COUNT(CASE WHEN status = 'published' THEN 1 END) as published,
                COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled,
                COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent
            FROM marketing_content
        """)
        
        content_stats = cur.fetchone()
        
        # Get platform distribution
        cur.execute("""
            SELECT platform, COUNT(*) as count
            FROM marketing_content
            WHERE status = 'published'
            GROUP BY platform
        """)
        
        platform_stats = cur.fetchall()
        
        # Get engagement metrics
        cur.execute("""
            SELECT 
                SUM(likes) as total_likes,
                SUM(shares) as total_shares,
                SUM(comments) as total_comments,
                AVG(engagement_rate) as avg_engagement_rate
            FROM content_engagement_metrics
            WHERE recorded_at >= CURRENT_DATE - INTERVAL '30 days'
        """)
        
        engagement_stats = cur.fetchone()
        
        conn.close()
        
        return {
            'content_statistics': dict(content_stats) if content_stats else {},
            'platform_distribution': [dict(stat) for stat in platform_stats],
            'engagement_metrics': dict(engagement_stats) if engagement_stats else {},
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting marketing dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("🎨 ChatterFix Marketing Studio starting...")
    uvicorn.run(app, host="0.0.0.0", port=8009)