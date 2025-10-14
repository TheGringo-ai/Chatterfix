#!/usr/bin/env python3
"""
ChatterFix Technician AI Assistant MVP
Standalone AI assistant for individual technicians
Showcases ChatterFix AI capabilities while driving leads
"""

from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
import json
import os
from datetime import datetime, timedelta
import httpx

# Configuration - Use environment variables for production
AI_BRAIN_URL = os.getenv("AI_BRAIN_URL", "http://localhost:9000")
PORT = int(os.getenv("PORT", 8085))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI_DIRECT = os.getenv("USE_OPENAI_DIRECT", "false").lower() == "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def call_ai_service(prompt: str, context: str = "maintenance") -> str:
    """Call AI service - either local brain or OpenAI direct"""
    if USE_OPENAI_DIRECT and OPENAI_API_KEY:
        # Use OpenAI directly for production
        try:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are Fix It Fred, a friendly and experienced maintenance technician AI assistant. Always introduce yourself as Fred and sign off with '- Fred'. Context: {context}"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "Hello! I'm Fix It Fred, but I'm having trouble connecting to my AI brain right now. Please try again later. - Fred"
    else:
        # Use local AI brain service
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{AI_BRAIN_URL}/api/ai/chat",
                    json={"message": prompt, "context": context}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "Sorry, I couldn't process that request.")
        except Exception as e:
            logger.error(f"AI brain service error: {e}")
            return "Hello! I'm Fix It Fred, but I'm having trouble connecting to my AI brain right now. Please try again later. - Fred"

app = FastAPI(
    title="Fix It Fred - AI Maintenance Assistant",
    description="Your Personal AI Maintenance Expert Named Fred - Available 24/7",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TroubleshootingQuery(BaseModel):
    equipment: str
    issue_description: str
    voice_input: Optional[str] = None
    technician_id: Optional[str] = None

class PhotoAnalysisRequest(BaseModel):
    image_data: str  # Base64 encoded
    equipment_type: Optional[str] = None
    technician_id: Optional[str] = None

class WorkNote(BaseModel):
    content: str
    equipment_id: Optional[str] = None
    voice_input: Optional[str] = None
    technician_id: Optional[str] = None

class VoiceProcessingRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: Optional[str] = "en-US"
    enhance_audio: Optional[bool] = True
    technician_id: Optional[str] = None

class JobEstimateRequest(BaseModel):
    project_name: str
    project_type: str  # "home_repair", "renovation", "construction", "maintenance"
    description: str
    location: Optional[str] = None
    photos: Optional[List[str]] = []  # Base64 encoded photos
    timeline_needed: Optional[str] = None
    technician_id: Optional[str] = None

class SignupRequest(BaseModel):
    email: str
    name: Optional[str] = None
    user_type: str  # "homeowner", "contractor", "technician", "other"
    company: Optional[str] = None
    phone: Optional[str] = None
    interests: Optional[List[str]] = []  # "troubleshooting", "estimation", "project_planning"

class TechnicianProfile(BaseModel):
    name: str
    specialties: List[str]
    experience_years: int
    primary_equipment: List[str]

# In-memory storage (replace with database in production)
technician_profiles = {}
work_notes = {}
equipment_history = {}

@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Fix It Fred - Professional Landing Page with Signup"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fix It Fred - AI Maintenance Assistant | Free Trial</title>
        <meta name="description" content="Meet Fred, your AI maintenance expert! Get instant troubleshooting, job estimates, and project planning. Free trial available.">
        <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        
        /* Hero Section */
        .hero {
            background: linear-gradient(135deg, #006fee 0%, #4285f4 100%);
            color: white;
            padding: 4rem 2rem;
            text-align: center;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .hero h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            line-height: 1.2;
        }
        .hero .tagline {
            font-size: 1.4rem;
            margin-bottom: 2rem;
            opacity: 0.95;
        }
        .hero .description {
            font-size: 1.1rem;
            margin-bottom: 3rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
            opacity: 0.9;
        }
        
        /* Signup Form */
        .signup-form {
            background: rgba(255,255,255,0.95);
            color: #333;
            padding: 2rem;
            border-radius: 20px;
            max-width: 500px;
            margin: 0 auto 2rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        .signup-form h2 {
            color: #006fee;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #555;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 0.8rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #006fee;
        }
        .checkbox-group {
            margin: 1rem 0;
        }
        .checkbox-group label {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            font-weight: normal;
        }
        .checkbox-group input[type="checkbox"] {
            width: auto;
            margin-right: 0.5rem;
        }
        .signup-btn {
            width: 100%;
            background: #006fee;
            color: white;
            padding: 1rem;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        .signup-btn:hover {
            background: #0056cc;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,111,238,0.3);
        }
        
        /* Features Section */
        .features {
            padding: 4rem 2rem;
            background: #f8fafc;
        }
        .features h2 {
            text-align: center;
            color: #1a202c;
            margin-bottom: 3rem;
            font-size: 2.5rem;
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .feature-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .feature-card h3 {
            color: #1a202c;
            margin-bottom: 1rem;
        }
        .feature-card p {
            color: #4a5568;
        }
        
        /* Demo Section */
        .demo {
            padding: 4rem 2rem;
            background: white;
            text-align: center;
        }
        .demo h2 {
            color: #1a202c;
            margin-bottom: 2rem;
            font-size: 2.5rem;
        }
        .demo-container {
            max-width: 600px;
            margin: 0 auto;
            background: #f8fafc;
            padding: 2rem;
            border-radius: 20px;
        }
        .demo-input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 50px;
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        .demo-btn {
            background: #006fee;
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .demo-btn:hover {
            background: #0056cc;
        }
        
        /* Pricing Section */
        .pricing {
            padding: 4rem 2rem;
            background: #1a202c;
            color: white;
            text-align: center;
        }
        .pricing h2 {
            margin-bottom: 3rem;
            font-size: 2.5rem;
        }
        .pricing-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            max-width: 1000px;
            margin: 0 auto;
        }
        .pricing-card {
            background: white;
            color: #333;
            padding: 2rem;
            border-radius: 15px;
            position: relative;
        }
        .pricing-card.featured {
            border: 3px solid #006fee;
            transform: scale(1.05);
        }
        .pricing-card h3 {
            color: #006fee;
            margin-bottom: 1rem;
        }
        .price {
            font-size: 2rem;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 1rem;
        }
        .pricing-features {
            list-style: none;
            margin-bottom: 2rem;
        }
        .pricing-features li {
            padding: 0.5rem 0;
            border-bottom: 1px solid #e1e5e9;
        }
        
        /* Footer */
        .footer {
            background: #006fee;
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            .hero h1 { font-size: 2.5rem; }
            .hero .tagline { font-size: 1.2rem; }
            .features h2, .demo h2, .pricing h2 { font-size: 2rem; }
            .signup-form { margin: 0 1rem 2rem; padding: 1.5rem; }
            .pricing-card.featured { transform: none; }
        }
        </style>
    </head>
    <body>
        <!-- Hero Section -->
        <section class="hero">
            <h1>🔧 Meet Fix It Fred</h1>
            <p class="tagline">Your Personal AI Maintenance Expert</p>
            <p class="description">
                From fixing broken equipment to estimating renovation costs, Fred combines decades of maintenance expertise with cutting-edge AI. 
                Perfect for homeowners, contractors, and maintenance professionals.
            </p>
            
            <!-- Signup Form -->
            <div class="signup-form">
                <h2>Start Your Free Trial Today!</h2>
                <form id="signupForm">
                    <div class="form-group">
                        <label for="email">Email Address *</label>
                        <input type="email" id="email" name="email" required placeholder="your@email.com">
                    </div>
                    
                    <div class="form-group">
                        <label for="name">Full Name</label>
                        <input type="text" id="name" name="name" placeholder="John Smith">
                    </div>
                    
                    <div class="form-group">
                        <label for="userType">I am a... *</label>
                        <select id="userType" name="userType" required>
                            <option value="">Select one</option>
                            <option value="homeowner">Homeowner / DIY Enthusiast</option>
                            <option value="contractor">Contractor / Construction Pro</option>
                            <option value="technician">Maintenance Technician</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="company">Company (Optional)</label>
                        <input type="text" id="company" name="company" placeholder="Your Company Name">
                    </div>
                    
                    <div class="checkbox-group">
                        <label>I'm interested in:</label>
                        <label><input type="checkbox" name="interests" value="troubleshooting"> Equipment Troubleshooting</label>
                        <label><input type="checkbox" name="interests" value="estimation"> Job Cost Estimation</label>
                        <label><input type="checkbox" name="interests" value="planning"> Project Planning</label>
                        <label><input type="checkbox" name="interests" value="maintenance"> Maintenance Management</label>
                    </div>
                    
                    <button type="submit" class="signup-btn">🚀 Get My Free Fred Account</button>
                    <p style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.8;">
                        No credit card required • 14-day free trial • Cancel anytime
                    </p>
                </form>
            </div>
            
            <p style="margin-top: 2rem; opacity: 0.9;">
                ⭐ Trusted by 10,000+ maintenance professionals and homeowners
            </p>
        </section>
        
        <!-- Features Section -->
        <section class="features">
            <h2>Why Choose Fix It Fred?</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <h3>AI-Powered Expertise</h3>
                    <p>Fred combines decades of maintenance knowledge with cutting-edge AI to solve any problem you throw at him.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💰</div>
                    <h3>Instant Cost Estimates</h3>
                    <p>Get accurate project estimates in seconds. From simple repairs to full renovations, Fred knows the costs.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📷</div>
                    <h3>Photo Analysis</h3>
                    <p>Snap a picture of broken equipment or project plans. Fred can see what you see and provide expert guidance.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎤</div>
                    <h3>Voice Commands</h3>
                    <p>Just talk to Fred like a colleague. Voice-to-text technology captures every detail of your maintenance needs.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📋</div>
                    <h3>Project Planning</h3>
                    <p>From timeline optimization to resource scheduling, Fred helps you plan projects like a seasoned pro.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <h3>Personal Memory</h3>
                    <p>Fred remembers your equipment, preferences, and project history to provide increasingly personalized advice.</p>
                </div>
            </div>
        </section>
        
        <!-- Demo Section -->
        <section class="demo">
            <h2>Try Fred Right Now!</h2>
            <div class="demo-container">
                <input type="text" class="demo-input" id="demoInput" 
                       placeholder="Ask Fred: 'Estimate kitchen renovation costs' or 'My pump is making noise'">
                <button class="demo-btn" onclick="demoQuery()">Ask Fred</button>
                <div id="demoResponse" style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 10px; display: none;"></div>
            </div>
        </section>
        
        <!-- Pricing Section -->
        <section class="pricing">
            <h2>Simple, Transparent Pricing</h2>
            <div class="pricing-cards">
                <div class="pricing-card">
                    <h3>Fred Free</h3>
                    <div class="price">$0/month</div>
                    <ul class="pricing-features">
                        <li>✅ Basic troubleshooting</li>
                        <li>✅ 3 cost estimates/month</li>
                        <li>✅ Photo analysis</li>
                        <li>❌ Voice features</li>
                        <li>❌ Project planning</li>
                        <li>❌ Personal memory</li>
                    </ul>
                    <button class="signup-btn">Start Free</button>
                </div>
                
                <div class="pricing-card featured">
                    <h3>Fred Pro</h3>
                    <div class="price">$19.99/month</div>
                    <ul class="pricing-features">
                        <li>✅ Everything in Free</li>
                        <li>✅ Unlimited estimates</li>
                        <li>✅ Voice-to-text</li>
                        <li>✅ Project planning</li>
                        <li>✅ Personal equipment memory</li>
                        <li>✅ Priority support</li>
                    </ul>
                    <button class="signup-btn">Start 14-Day Trial</button>
                </div>
                
                <div class="pricing-card">
                    <h3>Fred Business</h3>
                    <div class="price">$49.99/month</div>
                    <ul class="pricing-features">
                        <li>✅ Everything in Pro</li>
                        <li>✅ Team collaboration</li>
                        <li>✅ Client management</li>
                        <li>✅ Advanced analytics</li>
                        <li>✅ Supplier integration</li>
                        <li>✅ Custom branding</li>
                    </ul>
                    <button class="signup-btn">Start Business Trial</button>
                </div>
            </div>
        </section>
        
        <!-- Footer -->
        <footer class="footer">
            <p>Powered by <strong>ChatterFix AI</strong> - The Future of Maintenance Management</p>
            <p style="margin-top: 1rem;">
                <a href="https://chatterfix.com" style="color: rgba(255,255,255,0.8);">Learn about ChatterFix CMMS Platform →</a>
            </p>
        </footer>
        
        <script>
        // Signup Form Handler
        document.getElementById('signupForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const interests = Array.from(document.querySelectorAll('input[name="interests"]:checked')).map(cb => cb.value);
            
            const signupData = {
                email: formData.get('email'),
                name: formData.get('name'),
                user_type: formData.get('userType'),
                company: formData.get('company'),
                interests: interests
            };
            
            try {
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(signupData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('🎉 Welcome to Fix It Fred! Check your email for next steps.');
                    e.target.reset();
                } else {
                    alert('Signup failed. Please try again.');
                }
            } catch (error) {
                alert('Network error. Please check your connection and try again.');
            }
        });
        
        // Demo Function
        async function demoQuery() {
            const input = document.getElementById('demoInput');
            const response = document.getElementById('demoResponse');
            const query = input.value.trim();
            
            if (!query) return;
            
            response.style.display = 'block';
            response.innerHTML = '🔧 Fred is thinking...';
            
            try {
                const result = await fetch('/api/troubleshoot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        equipment: 'Unknown',
                        issue_description: query,
                        voice_input: query
                    })
                });
                
                const data = await result.json();
                response.innerHTML = `
                    <strong>🔧 Fred says:</strong><br>
                    ${data.response || 'I can help with that! Sign up above for detailed guidance.'}
                    <br><br>
                    <small><em>This is just a preview - Sign up above for full access!</em></small>
                `;
            } catch (error) {
                response.innerHTML = `
                    <strong>🔧 Fred says:</strong><br>
                    I can help you with that! Sign up above for detailed AI-powered assistance.
                `;
            }
        }
        
        // Enter key support for demo
        document.getElementById('demoInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                demoQuery();
            }
        });
        </script>
    </body>
    </html>
    """

@app.post("/api/troubleshoot")
async def troubleshoot_equipment(query: TroubleshootingQuery):
    """AI-powered troubleshooting assistance"""
    try:
        # Basic troubleshooting logic (enhance with actual AI integration)
        response = await generate_troubleshooting_response(query)
        
        # Store query for learning (in production, use proper database)
        store_troubleshooting_query(query)
        
        return {
            "success": True,
            "response": response,
            "troubleshooting_steps": generate_steps(query.issue_description),
            "estimated_time": "5-15 minutes",
            "confidence": 0.85
        }
    except Exception as e:
        logger.error(f"Troubleshooting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-photo")
async def analyze_equipment_photo(file: UploadFile = File(...)):
    """AI-powered equipment photo analysis with OCR"""
    try:
        # Read file content
        content = await file.read()
        
        # Process with ChatterFix Document Intelligence
        async with httpx.AsyncClient() as client:
            # Prepare multipart form data
            files = {"file": (file.filename, content, file.content_type)}
            data = {"analysis_types": '["ocr", "equipment_identification"]'}
            
            # Call Document Intelligence API
            response = await client.post(
                "https://chatterfix-document-intelligence-650169261019.us-central1.run.app/api/process-document",
                files=files,
                data=data,
                timeout=45.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract analysis data
                equipment_data = result.get("extracted_data", {}).get("equipment", {})
                ocr_results = result.get("ocr_results", {})
                
                # Enhanced analysis with AI
                analysis_prompt = f"""Analyze this equipment photo data:
                
Equipment Detected: {equipment_data.get('equipment_type', 'Unknown')}
Text from Image: {ocr_results.get('full_text', 'No text detected')}
Confidence: {equipment_data.get('confidence', 0)}

Based on this data, identify potential issues, maintenance needs, and provide specific recommendations for a technician."""

                # Get AI analysis
                ai_response = await client.post(
                    f"{AI_BRAIN_URL}/api/ai/chat",
                    json={
                        "message": analysis_prompt,
                        "context": "equipment_photo_analysis"
                    },
                    timeout=30.0
                )
                
                ai_analysis = ""
                if ai_response.status_code == 200:
                    ai_data = ai_response.json()
                    ai_analysis = ai_data.get("response", "")
                
                return {
                    "success": True,
                    "analysis": {
                        "equipment_detected": equipment_data.get("equipment_type", "Equipment"),
                        "model": equipment_data.get("model", "Unknown"),
                        "manufacturer": equipment_data.get("manufacturer", "Unknown"),
                        "text_found": ocr_results.get("full_text", "")[:500],  # Limit for display
                        "ai_analysis": ai_analysis,
                        "confidence": equipment_data.get("confidence", 0.75),
                        "processing_time": result.get("processing_time", "unknown")
                    },
                    "document_id": result.get("document_id"),
                    "recommendations": extract_recommendations(ai_analysis)
                }
            else:
                # Fallback to basic analysis
                return get_fallback_photo_analysis(file.filename)
                
    except Exception as e:
        logger.error(f"Photo analysis error: {e}", exc_info=True)
        return get_fallback_photo_analysis(file.filename or "photo")

def extract_recommendations(ai_analysis: str) -> list:
    """Extract recommendations from AI analysis"""
    if not ai_analysis:
        return ["Upload photo for detailed AI analysis", "Check equipment manual", "Consult maintenance expert"]
    
    # Simple extraction - look for numbered lists or bullet points
    lines = ai_analysis.split('\n')
    recommendations = []
    
    for line in lines:
        line = line.strip()
        if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•']):
            clean_rec = line.lstrip('1234567890.-• ').strip()
            if clean_rec and len(clean_rec) > 10:
                recommendations.append(clean_rec)
    
    return recommendations[:5] if recommendations else [
        "Follow standard maintenance procedures",
        "Document current condition", 
        "Schedule follow-up inspection"
    ]

def get_fallback_photo_analysis(filename: str):
    """Fallback photo analysis when OCR service unavailable"""
    return {
        "success": True,
        "analysis": {
            "equipment_detected": "Equipment (from filename)",
            "model": "Unknown - OCR processing needed",
            "manufacturer": "Unknown",
            "text_found": "",
            "ai_analysis": "🔧 Basic photo received! For detailed AI-powered equipment identification, OCR text extraction, and maintenance recommendations, upgrade to TechBot Pro with live Document Intelligence processing.",
            "confidence": 0.5,
            "processing_time": "offline"
        },
        "document_id": f"offline_{datetime.now().timestamp()}",
        "recommendations": [
            "💡 Upgrade to TechBot Pro for AI photo analysis",
            "Check equipment nameplate manually",
            "Reference equipment documentation",
            "Contact maintenance specialist if needed"
        ]
    }

@app.post("/api/voice-to-text")
async def process_voice_to_text(file: UploadFile = File(...)):
    """Convert voice recordings to text using Document Intelligence"""
    try:
        # Read audio file content
        content = await file.read()
        
        # Process with ChatterFix Document Intelligence
        async with httpx.AsyncClient() as client:
            # Prepare multipart form data for voice processing
            files = {"file": (file.filename, content, file.content_type)}
            data = {
                "language": "en-US",
                "enhance_audio": "true"
            }
            
            # Call Document Intelligence voice-to-document API
            response = await client.post(
                "https://chatterfix-document-intelligence-650169261019.us-central1.run.app/api/voice-to-document",
                files=files,
                data=data,
                timeout=60.0  # Voice processing can take longer
            )
            
            if response.status_code == 200:
                result = response.json()
                transcription_data = result.get("transcription", {})
                
                # Extract transcribed text
                transcribed_text = transcription_data.get("text", "")
                confidence = transcription_data.get("confidence", 0.0)
                
                # Optional: Enhance with AI for technical context
                if transcribed_text:
                    ai_prompt = f"""Review this technician voice note and improve it for clarity:

Original: {transcribed_text}

Make it more professional and clear while preserving all technical details. Format as a proper work note."""

                    try:
                        ai_response = await client.post(
                            f"{AI_BRAIN_URL}/api/ai/chat",
                            json={
                                "message": ai_prompt,
                                "context": "voice_note_enhancement"
                            },
                            timeout=30.0
                        )
                        
                        enhanced_text = transcribed_text
                        if ai_response.status_code == 200:
                            ai_data = ai_response.json()
                            enhanced_text = ai_data.get("response", transcribed_text)
                    except:
                        enhanced_text = transcribed_text
                
                return {
                    "success": True,
                    "transcription": {
                        "original_text": transcribed_text,
                        "enhanced_text": enhanced_text,
                        "confidence": confidence,
                        "language": transcription_data.get("language", "en-US"),
                        "duration": transcription_data.get("duration", "unknown"),
                        "processing_time": result.get("processing_time", "unknown")
                    },
                    "document_id": result.get("document_id"),
                    "suggestions": generate_voice_suggestions(enhanced_text)
                }
            else:
                # Fallback for voice processing
                return get_fallback_voice_processing(file.filename)
                
    except Exception as e:
        logger.error(f"Voice processing error: {e}", exc_info=True)
        return get_fallback_voice_processing(file.filename or "audio")

def generate_voice_suggestions(text: str) -> list:
    """Generate suggestions based on voice transcription"""
    if not text:
        return ["🎤 Record voice notes for instant transcription", "📝 Create work orders from voice", "🔧 Log maintenance activities"]
    
    suggestions = []
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["check", "inspect", "look"]):
        suggestions.append("🔍 Schedule follow-up inspection")
    
    if any(word in text_lower for word in ["replace", "repair", "fix"]):
        suggestions.append("🔧 Add to maintenance schedule")
    
    if any(word in text_lower for word in ["order", "part", "component"]):
        suggestions.append("📦 Check parts inventory")
    
    if any(word in text_lower for word in ["urgent", "emergency", "immediate"]):
        suggestions.append("🚨 Create urgent work order")
    
    return suggestions[:3] if suggestions else [
        "📝 Save as work note",
        "📋 Add to equipment history",
        "🔔 Set reminder"
    ]

def get_fallback_voice_processing(filename: str):
    """Fallback when voice processing is unavailable"""
    return {
        "success": True,
        "transcription": {
            "original_text": "",
            "enhanced_text": "🎤 Voice file received! For real-time speech-to-text transcription, AI enhancement, and technical terminology recognition, upgrade to TechBot Pro with live Document Intelligence processing.",
            "confidence": 0.0,
            "language": "en-US",
            "duration": "unknown",
            "processing_time": "offline"
        },
        "document_id": f"voice_offline_{datetime.now().timestamp()}",
        "suggestions": [
            "💡 Upgrade to TechBot Pro for voice transcription",
            "🎤 Try recording shorter audio clips",
            "📝 Use text input as alternative",
            "🔧 Check microphone settings"
        ]
    }

@app.post("/api/work-note")
async def create_work_note(note: WorkNote):
    """Create voice-to-text work notes"""
    try:
        # Process work note
        note_id = f"note_{datetime.now().timestamp()}"
        
        # Store note (in production, use proper database)
        work_notes[note_id] = {
            "content": note.content,
            "timestamp": datetime.now().isoformat(),
            "equipment_id": note.equipment_id,
            "technician_id": note.technician_id
        }
        
        return {
            "success": True,
            "note_id": note_id,
            "processed_content": note.content,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Work note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/technician/profile")
async def create_update_technician_profile(profile: TechnicianProfile):
    """Create or update technician profile for personalized experience"""
    try:
        profile_id = f"tech_{profile.name.lower().replace(' ', '_')}"
        
        # Store profile (in production, use proper database)
        technician_profiles[profile_id] = {
            "name": profile.name,
            "specialties": profile.specialties,
            "experience_years": profile.experience_years,
            "primary_equipment": profile.primary_equipment,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_interactions": 0,
            "equipment_worked_on": []
        }
        
        return {
            "success": True,
            "profile_id": profile_id,
            "message": f"Profile created for {profile.name}",
            "personalization_enabled": True
        }
    except Exception as e:
        logger.error(f"Profile creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/technician/{technician_id}/history")
async def get_technician_history(technician_id: str):
    """Get technician's equipment history and interactions"""
    try:
        # Get profile
        profile = technician_profiles.get(technician_id, {})
        if not profile:
            return {"success": False, "message": "Technician profile not found"}
        
        # Get equipment history
        tech_equipment = equipment_history.get(technician_id, [])
        
        # Get recent work notes
        tech_notes = {k: v for k, v in work_notes.items() 
                     if v.get("technician_id") == technician_id}
        
        return {
            "success": True,
            "technician": {
                "name": profile.get("name"),
                "specialties": profile.get("specialties", []),
                "experience_years": profile.get("experience_years", 0),
                "total_interactions": profile.get("total_interactions", 0)
            },
            "equipment_history": tech_equipment[-10:],  # Last 10 equipment
            "recent_notes": list(tech_notes.values())[-5:],  # Last 5 notes
            "recommendations": generate_personalized_recommendations(profile, tech_equipment)
        }
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/technician/{technician_id}/equipment")
async def add_equipment_to_history(technician_id: str, equipment_data: dict):
    """Add equipment to technician's memory"""
    try:
        # Initialize if needed
        if technician_id not in equipment_history:
            equipment_history[technician_id] = []
        
        # Add equipment with timestamp
        equipment_entry = {
            "equipment_type": equipment_data.get("equipment_type", "Unknown"),
            "model": equipment_data.get("model", ""),
            "serial_number": equipment_data.get("serial_number", ""),
            "location": equipment_data.get("location", ""),
            "last_interaction": datetime.now().isoformat(),
            "interaction_type": equipment_data.get("interaction_type", "troubleshooting"),
            "notes": equipment_data.get("notes", "")
        }
        
        equipment_history[technician_id].append(equipment_entry)
        
        # Update profile interaction count
        if technician_id in technician_profiles:
            technician_profiles[technician_id]["total_interactions"] += 1
            technician_profiles[technician_id]["last_updated"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "Equipment added to technician memory",
            "total_equipment": len(equipment_history[technician_id])
        }
    except Exception as e:
        logger.error(f"Equipment memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/technician/{technician_id}/recommendations")
async def get_personalized_recommendations(technician_id: str):
    """Get AI-powered personalized recommendations based on history"""
    try:
        profile = technician_profiles.get(technician_id, {})
        tech_equipment = equipment_history.get(technician_id, [])
        
        if not profile:
            return {"success": False, "message": "Technician profile not found"}
        
        # Generate AI-powered recommendations
        context = f"""Technician Profile:
- Name: {profile.get('name')}
- Specialties: {', '.join(profile.get('specialties', []))}
- Experience: {profile.get('experience_years')} years
- Recent Equipment: {[eq.get('equipment_type') for eq in tech_equipment[-5:]]}

Generate personalized maintenance recommendations and learning suggestions."""

        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                f"{AI_BRAIN_URL}/api/ai/chat",
                json={
                    "message": context,
                    "context": "personalized_recommendations"
                },
                timeout=30.0
            )
            
            ai_recommendations = ""
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                ai_recommendations = ai_data.get("response", "")
        
        return {
            "success": True,
            "recommendations": {
                "ai_suggestions": ai_recommendations,
                "equipment_focus": generate_equipment_focus(tech_equipment),
                "skill_development": generate_skill_suggestions(profile),
                "upcoming_maintenance": generate_maintenance_alerts(tech_equipment)
            }
        }
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_personalized_recommendations(profile: dict, equipment_history: list) -> list:
    """Generate personalized recommendations based on technician history"""
    recommendations = []
    
    # Based on experience level
    experience = profile.get("experience_years", 0)
    if experience < 2:
        recommendations.append("📚 Review safety procedures for your specialty areas")
    elif experience < 5:
        recommendations.append("🔧 Consider advanced troubleshooting certification")
    else:
        recommendations.append("👨‍🏫 Share knowledge with junior technicians")
    
    # Based on recent equipment
    if equipment_history:
        recent_types = [eq.get("equipment_type") for eq in equipment_history[-3:]]
        most_common = max(set(recent_types), key=recent_types.count) if recent_types else None
        if most_common:
            recommendations.append(f"🎯 Focus on {most_common} preventive maintenance")
    
    # Based on specialties
    specialties = profile.get("specialties", [])
    if "electrical" in [s.lower() for s in specialties]:
        recommendations.append("⚡ Review electrical safety updates")
    
    return recommendations[:3]

def generate_equipment_focus(equipment_history: list) -> list:
    """Generate equipment focus areas based on history"""
    if not equipment_history:
        return ["🔧 Start building equipment experience"]
    
    equipment_types = [eq.get("equipment_type", "Unknown") for eq in equipment_history]
    type_counts = {}
    for eq_type in equipment_types:
        type_counts[eq_type] = type_counts.get(eq_type, 0) + 1
    
    # Sort by frequency
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    return [f"🎯 {eq_type} ({count} interactions)" for eq_type, count in sorted_types[:3]]

def generate_skill_suggestions(profile: dict) -> list:
    """Generate skill development suggestions"""
    experience = profile.get("experience_years", 0)
    specialties = profile.get("specialties", [])
    
    suggestions = []
    
    if experience < 3:
        suggestions.append("📖 Basic equipment troubleshooting course")
        suggestions.append("🛡️ Safety certification renewal")
    else:
        suggestions.append("🔬 Advanced diagnostic techniques")
        suggestions.append("💻 Digital maintenance tools training")
    
    # Add specialty-specific suggestions
    if not any("electrical" in s.lower() for s in specialties):
        suggestions.append("⚡ Basic electrical systems training")
    
    return suggestions[:3]

def generate_maintenance_alerts(equipment_history: list) -> list:
    """Generate maintenance alerts based on equipment history"""
    if not equipment_history:
        return ["📋 No maintenance alerts - start documenting equipment"]
    
    alerts = []
    now = datetime.now()
    
    for equipment in equipment_history[-5:]:  # Check last 5 equipment
        last_interaction = equipment.get("last_interaction", "")
        if last_interaction:
            try:
                last_date = datetime.fromisoformat(last_interaction.replace('Z', '+00:00').replace('+00:00', ''))
                days_since = (now - last_date).days
                
                if days_since > 30:
                    alerts.append(f"⚠️ {equipment.get('equipment_type', 'Equipment')} - {days_since} days since last check")
            except:
                pass
    
    return alerts[:3] if alerts else ["✅ All equipment recently checked"]

@app.post("/api/signup")
async def handle_signup(request: SignupRequest):
    """Handle Fix It Fred signup and send notification to mailing list"""
    try:
        # Store signup in memory (in production, use proper database)
        signup_id = f"signup_{datetime.now().timestamp()}"
        
        signup_data = {
            "signup_id": signup_id,
            "email": request.email,
            "name": request.name,
            "user_type": request.user_type,
            "company": request.company,
            "phone": request.phone,
            "interests": request.interests,
            "signup_date": datetime.now().isoformat(),
            "status": "new_signup"
        }
        
        # Store locally (in production, this would go to a database)
        if "signups" not in globals():
            globals()["signups"] = {}
        globals()["signups"][signup_id] = signup_data
        
        # Send notification email to yoyofred@gringosgambit.com
        await send_signup_notification(signup_data)
        
        # Send welcome email to user (placeholder)
        await send_welcome_email(request.email, request.name)
        
        return {
            "success": True,
            "message": "Welcome to Fix It Fred! Check your email for next steps.",
            "signup_id": signup_id,
            "trial_expires": (datetime.now() + timedelta(days=14)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Signup failed. Please try again."
        }

async def send_signup_notification(signup_data: dict):
    """Send signup notification to yoyofred@gringosgambit.com"""
    try:
        # Email content for Fred's mailing list
        subject = f"🔧 New Fix It Fred Signup: {signup_data['user_type']} - {signup_data['email']}"
        
        body = f"""
🚀 NEW FIX IT FRED SIGNUP!

📧 Email: {signup_data['email']}
👤 Name: {signup_data.get('name', 'Not provided')}
🏷️ Type: {signup_data['user_type']}
🏢 Company: {signup_data.get('company', 'Not provided')}
📞 Phone: {signup_data.get('phone', 'Not provided')}

🎯 Interests:
{chr(10).join(['- ' + interest.title() for interest in signup_data.get('interests', [])])}

📅 Signup Date: {signup_data['signup_date']}
🆔 Signup ID: {signup_data['signup_id']}

💡 Lead Quality Score: {calculate_lead_score(signup_data)}/10

---
This is an automated notification from Fix It Fred.
Add this lead to your mailing list and follow up accordingly!
        """
        
        # Simulate email sending (in production, use proper email service)
        # await send_email(
        #     to="yoyofred@gringosgambit.com",
        #     subject=subject,
        #     body=body
        # )
        
        # Log for now (replace with actual email service)
        logger.info(f"SIGNUP NOTIFICATION: {subject}")
        logger.info(f"MAILING LIST EMAIL BODY: {body}")
        
    except Exception as e:
        logger.error(f"Failed to send signup notification: {e}")

async def send_welcome_email(email: str, name: str):
    """Send welcome email to new user"""
    try:
        # Welcome email content
        subject = "🔧 Welcome to Fix It Fred - Your AI Maintenance Expert!"
        
        body = f"""
Hi {name or 'there'}!

🎉 Welcome to Fix It Fred! I'm excited to be your personal AI maintenance expert.

🚀 HERE'S HOW TO GET STARTED:

1. 📱 Bookmark this link: [Your Fix It Fred Dashboard]
2. 🔧 Try asking me about any maintenance issue
3. 💰 Use the job estimation feature for your projects
4. 📷 Upload photos of equipment for instant analysis

💡 QUICK TIPS:
- Ask me: "Fred, estimate bathroom renovation costs"
- Upload photos of broken equipment for diagnosis
- Use voice notes for hands-free troubleshooting
- I remember your equipment and preferences over time

🎁 YOUR 14-DAY FREE TRIAL INCLUDES:
✅ Unlimited troubleshooting assistance
✅ Unlimited job cost estimates
✅ Photo analysis and OCR
✅ Voice-to-text features
✅ Personal equipment memory
✅ Project planning tools

Need help? Just reply to this email or ask me directly in the app!

Ready to fix anything that's broken? Let's get started!

- Fred 🔧

P.S. Don't forget to save my contact info - I'm available 24/7!

---
Fix It Fred - Powered by ChatterFix AI
https://chatterfix.com
        """
        
        # Simulate email sending (in production, use proper email service)
        logger.info(f"WELCOME EMAIL: {subject} to {email}")
        logger.info(f"WELCOME EMAIL BODY: {body}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")

def calculate_lead_score(signup_data: dict) -> int:
    """Calculate lead quality score for prioritization"""
    score = 5  # Base score
    
    # User type scoring
    if signup_data['user_type'] == 'contractor':
        score += 3  # High value
    elif signup_data['user_type'] == 'technician':
        score += 2  # Medium-high value
    elif signup_data['user_type'] == 'homeowner':
        score += 1  # Medium value
    
    # Company provided
    if signup_data.get('company'):
        score += 1
    
    # Phone provided
    if signup_data.get('phone'):
        score += 1
    
    # Multiple interests
    if len(signup_data.get('interests', [])) >= 3:
        score += 1
    
    return min(score, 10)  # Cap at 10

@app.get("/api/signups")
async def get_signups():
    """Get all signups for mailing list management"""
    try:
        if "signups" not in globals():
            return {"signups": [], "total": 0}
        
        signups = globals()["signups"]
        
        return {
            "signups": list(signups.values()),
            "total": len(signups),
            "summary": {
                "homeowners": len([s for s in signups.values() if s['user_type'] == 'homeowner']),
                "contractors": len([s for s in signups.values() if s['user_type'] == 'contractor']),
                "technicians": len([s for s in signups.values() if s['user_type'] == 'technician']),
                "others": len([s for s in signups.values() if s['user_type'] == 'other'])
            }
        }
    except Exception as e:
        logger.error(f"Failed to get signups: {e}")
        return {"signups": [], "total": 0}

@app.post("/api/estimate-job")
async def create_job_estimate(request: JobEstimateRequest):
    """Fred's AI-powered job planning and cost estimation"""
    try:
        # Enhanced AI prompt for Fred's estimation expertise
        estimation_prompt = f"""Hi! I'm Fix It Fred, your friendly AI construction and maintenance expert. Let me help you plan and estimate this project!

Project Details:
- Name: {request.project_name}
- Type: {request.project_type}
- Description: {request.description}
- Location: {request.location or 'Not specified'}
- Timeline: {request.timeline_needed or 'Flexible'}

As Fred, provide a comprehensive project estimate including:

1. **MATERIALS BREAKDOWN**
   - List all materials needed with quantities
   - Estimated costs per item (use 2024 pricing)
   - Recommended suppliers/brands

2. **LABOR ESTIMATION**
   - Skill levels required
   - Estimated hours by trade
   - Labor cost calculations

3. **PROJECT TIMELINE**
   - Phase breakdown
   - Critical path milestones
   - Weather/seasonal considerations

4. **COST SUMMARY**
   - Materials total
   - Labor total
   - 15% contingency
   - Grand total estimate

5. **FRED'S PRO TIPS**
   - Money-saving suggestions
   - Common pitfalls to avoid
   - Upgrade opportunities

Be specific, practical, and helpful. Sign off as "- Fred" and include upgrade prompts for advanced features."""

        # Get AI-powered estimation from Fred
        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                f"{AI_BRAIN_URL}/api/ai/chat",
                json={
                    "message": estimation_prompt,
                    "context": "job_estimation"
                },
                timeout=45.0
            )
            
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                fred_estimate = ai_data.get("response", "")
                
                # Generate additional structured data
                estimated_cost = estimate_project_cost(request)
                timeline_days = estimate_timeline(request)
                
                # Store in project history
                project_id = f"project_{datetime.now().timestamp()}"
                store_project_estimate(request, project_id, fred_estimate)
                
                return {
                    "success": True,
                    "project_id": project_id,
                    "estimate": {
                        "fred_analysis": fred_estimate,
                        "total_cost_estimate": estimated_cost,
                        "timeline_days": timeline_days,
                        "confidence_level": 0.85,
                        "created_by": "Fix It Fred AI"
                    },
                    "recommendations": extract_fred_recommendations(fred_estimate),
                    "next_steps": [
                        "📋 Review detailed breakdown",
                        "📞 Get supplier quotes", 
                        "📅 Schedule project phases",
                        "🔧 Upgrade to Fred Pro for advanced features"
                    ]
                }
            else:
                return get_fallback_estimation(request)
                
    except Exception as e:
        logger.error(f"Job estimation error: {e}", exc_info=True)
        return get_fallback_estimation(request)

def estimate_project_cost(request: JobEstimateRequest) -> dict:
    """Basic cost estimation algorithm"""
    base_costs = {
        "home_repair": {"materials": 500, "labor": 800},
        "renovation": {"materials": 5000, "labor": 8000}, 
        "construction": {"materials": 15000, "labor": 25000},
        "maintenance": {"materials": 200, "labor": 400}
    }
    
    base = base_costs.get(request.project_type, {"materials": 1000, "labor": 1500})
    
    # Complexity multiplier based on description length and keywords
    complexity = 1.0
    description_lower = request.description.lower()
    
    if any(word in description_lower for word in ["custom", "complex", "electrical", "plumbing"]):
        complexity *= 1.5
    if any(word in description_lower for word in ["simple", "basic", "minor"]):
        complexity *= 0.7
        
    materials_cost = int(base["materials"] * complexity)
    labor_cost = int(base["labor"] * complexity)
    contingency = int((materials_cost + labor_cost) * 0.15)
    
    return {
        "materials": materials_cost,
        "labor": labor_cost,
        "contingency": contingency,
        "total": materials_cost + labor_cost + contingency
    }

def estimate_timeline(request: JobEstimateRequest) -> int:
    """Estimate project timeline in days"""
    base_days = {
        "home_repair": 2,
        "renovation": 14,
        "construction": 60,
        "maintenance": 1
    }
    
    return base_days.get(request.project_type, 7)

def extract_fred_recommendations(fred_response: str) -> list:
    """Extract key recommendations from Fred's response"""
    recommendations = []
    lines = fred_response.split('\n')
    
    for line in lines:
        line = line.strip()
        if any(line.lower().startswith(word) for word in ['tip:', 'recommend', 'suggest', 'consider']):
            clean_rec = line.split(':', 1)[-1].strip()
            if clean_rec and len(clean_rec) > 20:
                recommendations.append(clean_rec)
    
    return recommendations[:5] if recommendations else [
        "Consider getting multiple supplier quotes",
        "Plan for 15% cost contingency",
        "Schedule inspections if required",
        "Upgrade to Fred Pro for detailed project management"
    ]

def store_project_estimate(request: JobEstimateRequest, project_id: str, estimate: str):
    """Store project estimate in memory"""
    # In production, this would go to a proper database
    if request.technician_id:
        if request.technician_id not in equipment_history:
            equipment_history[request.technician_id] = []
        
        project_entry = {
            "project_id": project_id,
            "project_name": request.project_name,
            "project_type": request.project_type,
            "description": request.description,
            "estimate": estimate,
            "created_at": datetime.now().isoformat(),
            "status": "estimated"
        }
        
        equipment_history[request.technician_id].append(project_entry)

def get_fallback_estimation(request: JobEstimateRequest):
    """Fallback estimation when AI is unavailable"""
    estimated_cost = estimate_project_cost(request)
    
    return {
        "success": True,
        "project_id": f"offline_{datetime.now().timestamp()}",
        "estimate": {
            "fred_analysis": f"🔧 Hi there! Fred here. I've created a basic estimate for your {request.project_name}. For detailed AI-powered analysis with material breakdowns, labor calculations, and timeline optimization, upgrade to Fix It Fred Pro!",
            "total_cost_estimate": estimated_cost,
            "timeline_days": estimate_timeline(request),
            "confidence_level": 0.6,
            "created_by": "Fix It Fred (Basic Mode)"
        },
        "recommendations": [
            "💡 Upgrade to Fred Pro for detailed estimates",
            "📸 Take photos for more accurate material calculations",
            "🎤 Use voice to describe complex projects",
            "📋 Get professional consultation for large projects"
        ],
        "next_steps": [
            "📋 Review basic estimate",
            "🚀 Upgrade to Fred Pro for advanced features",
            "📞 Consult with local contractors",
            "📅 Plan project phases"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fix-it-fred",
        "version": "1.0.0",
        "assistant_name": "Fix It Fred",
        "features": [
            "AI-powered troubleshooting with Fred's expertise",
            "Equipment photo analysis with OCR", 
            "Voice-to-text work notes",
            "Personal equipment memory system",
            "Job planning and cost estimation",
            "Project timeline optimization"
        ],
        "personality": "Friendly, experienced maintenance technician",
        "timestamp": datetime.now().isoformat()
    }

async def generate_troubleshooting_response(query: TroubleshootingQuery):
    """Generate AI-powered troubleshooting response"""
    try:
        # Integrate with ChatterFix AI brain service
        ai_prompt = f"""You are Fix It Fred, a friendly and experienced maintenance technician AI assistant. Always introduce yourself as Fred and maintain a helpful, professional personality.
        
Equipment: {query.equipment}
Issue: {query.issue_description}
        
As Fred, provide practical, step-by-step troubleshooting guidance. Be specific, safety-focused, and actionable. 
Include:
1. Immediate safety checks
2. Diagnostic steps in logical order
3. Common causes for this type of issue
4. Tools or measurements needed
5. When to call for backup/specialist

Keep response concise but thorough. Focus on what a technician can actually do in the field. Sign off as "- Fred" at the end."""

        async with httpx.AsyncClient() as client:
            ai_response = await client.post(
                f"{AI_BRAIN_URL}/api/ai/chat",
                json={
                    "message": ai_prompt,
                    "context": "technician_troubleshooting"
                },
                timeout=30.0
            )
            
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                ai_content = ai_data.get("response", "")
                
                # Add Fred signature and CTA
                return f"{ai_content}\n\n💡 Need more advanced diagnostics? Upgrade to Fix It Fred Pro for equipment-specific manuals, AR guidance, and predictive maintenance insights!"
            else:
                logger.warning(f"AI service error: {ai_response.status_code}")
                return get_fallback_response(query)
                
    except Exception as e:
        logger.error(f"AI integration error: {e}", exc_info=True)
        return get_fallback_response(query)

def get_fallback_response(query: TroubleshootingQuery):
    """Fallback response when AI service is unavailable"""
    issue = query.issue_description.lower()
    
    if "noise" in issue or "sound" in issue:
        return "🔧 Hey there! Fred here. Let's diagnose that noise! First, ensure safety - stop equipment if unsafe. Describe the sound: grinding, squealing, or rattling? Check: 1) Lubrication levels, 2) Belt tension, 3) Bearing condition. 🚀 For AI-powered audio analysis, upgrade to Fix It Fred Pro! - Fred"
    
    elif "overheating" in issue or "hot" in issue:
        return "🌡️ Fred here! Overheating detected! Safety first - allow cooling before inspection. Check: 1) Cooling system operation, 2) Blocked air vents, 3) Temperature readings vs normal range, 4) Excessive load conditions. 🚀 Get thermal imaging analysis with Fix It Fred Pro! - Fred"
    
    elif "leak" in issue:
        return "💧 Hi, it's Fred! Let's find that leak! Safety check for hazardous fluids first. Inspect: 1) All visible connections and seals, 2) Fluid levels and type, 3) Pressure readings if applicable. 📷 Take a photo - Fix It Fred Pro can identify leak sources from images! - Fred"
    
    else:
        return f"🔧 Hi there! Fred here. I can help troubleshoot your {query.equipment} issue! For detailed step-by-step guidance specific to your equipment model and real-time AI analysis, upgrade to Fix It Fred Pro. Basic troubleshooting: Check power, connections, settings, and recent changes. - Fred"

def generate_steps(issue_description: str):
    """Generate troubleshooting steps"""
    return [
        "Safety first - ensure equipment is in safe state",
        "Document current symptoms and conditions", 
        "Check obvious causes first (power, connections, settings)",
        "Use systematic diagnostic approach",
        "Document findings and actions taken"
    ]

def store_troubleshooting_query(query: TroubleshootingQuery):
    """Store troubleshooting query for learning"""
    # In production, this would go to a proper database
    logger.info(f"Troubleshooting query: {query.equipment} - {query.issue_description}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)