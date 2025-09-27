#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Advanced Feature Endpoints
Image upload, Speech-to-Text, OCR, AI Admin Dashboard
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, HTMLResponse
from typing import Dict, List, Any, Optional
import json
import base64
import io
from datetime import datetime
import asyncio

# Import our advanced modules
try:
    from advanced_media_system import AdvancedMediaSystem, advanced_media
    from ai_admin_dashboard import AIAdminDashboard, ai_admin
    ADVANCED_MODULES_AVAILABLE = True
except ImportError:
    ADVANCED_MODULES_AVAILABLE = False
    print("⚠️  Advanced modules not available")

def add_advanced_endpoints(app: FastAPI):
    """Add advanced feature endpoints to FastAPI app"""
    
    if not ADVANCED_MODULES_AVAILABLE:
        print("⚠️  Advanced endpoints not added - modules not available")
        return
    
    # ==================== IMAGE UPLOAD & MANAGEMENT ====================
    
    @app.post("/api/media/upload/image")
    async def upload_image(
        file: UploadFile = File(...),
        reference_type: str = Form(...),
        reference_id: int = Form(...),
        user_id: int = Form(1),  # Default user, would come from auth
        metadata: str = Form("{}")
    ):
        """Upload image with enhanced validation and error handling"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Enhanced file validation
            if not file.filename:
                raise HTTPException(status_code=400, detail="Filename is required")
                
            # Validate file type and extension
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            
            if not file.content_type or file.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")
            
            file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
            if f'.{file_ext}' not in allowed_extensions:
                raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
            
            # Check file size (limit to 10MB)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            file_data = await file.read()
            
            if len(file_data) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")
            
            if len(file_data) == 0:
                raise HTTPException(status_code=400, detail="Empty file not allowed")
            
            # Validate reference data
            if reference_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid reference_id")
                
            valid_reference_types = ['work_order', 'asset', 'part', 'user']
            if reference_type not in valid_reference_types:
                raise HTTPException(status_code=400, detail=f"Invalid reference_type. Allowed: {', '.join(valid_reference_types)}")
            
            # Parse and validate metadata
            try:
                metadata_dict = json.loads(metadata) if metadata else {}
                if not isinstance(metadata_dict, dict):
                    raise ValueError("Metadata must be a JSON object")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {str(e)}")
            
            # Enhanced security: Check for potentially malicious content
            # Basic magic number check for common image formats
            magic_numbers = {
                b'\xFF\xD8\xFF': 'jpeg',
                b'\x89PNG\r\n\x1a\n': 'png',
                b'GIF87a': 'gif',
                b'GIF89a': 'gif',
                b'RIFF': 'webp'
            }
            
            is_valid_image = False
            for magic, format_type in magic_numbers.items():
                if file_data.startswith(magic):
                    is_valid_image = True
                    break
            
            if not is_valid_image:
                raise HTTPException(status_code=400, detail="File content does not match image format")
            
            # Log upload attempt
            logger.info(f"Image upload started: {file.filename}, size: {len(file_data)}, user: {user_id}")
            
            # Upload and process image with transaction safety
            try:
                media_file = await advanced_media.upload_image(
                    image_data=file_data,
                    filename=file.filename,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    uploaded_by=user_id,
                    metadata=metadata_dict
                )
                
                logger.info(f"Image upload successful: {media_file.id}")
                
                return {
                    "success": True,
                    "file_id": media_file.id,
                    "filename": media_file.filename,
                    "file_size": media_file.file_size,
                    "content_type": file.content_type,
                    "reference_type": reference_type,
                    "reference_id": reference_id,
                    "message": "Image uploaded and processed successfully"
                }
                
            except Exception as upload_error:
                logger.error(f"Image upload failed: {str(upload_error)}")
                raise HTTPException(status_code=500, detail="Failed to process image upload")
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in image upload: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred during upload")
        finally:
            # Cleanup: Ensure file data is cleared from memory
            if 'file_data' in locals():
                del file_data
    
    @app.post("/api/media/upload/audio")
    async def upload_audio_for_transcription(
        file: UploadFile = File(...),
        reference_type: str = Form(...),
        reference_id: int = Form(...),
        user_id: int = Form(1)
    ):
        """Upload audio file for speech-to-text transcription"""
        try:
            # Validate audio file
            if not file.content_type or not file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="Invalid audio file")
            
            # Read file data
            file_data = await file.read()
            
            # Upload and transcribe
            media_file = await advanced_media.upload_audio_for_transcription(
                audio_data=file_data,
                filename=file.filename,
                reference_type=reference_type,
                reference_id=reference_id,
                uploaded_by=user_id
            )
            
            return {
                "success": True,
                "file_id": media_file.id,
                "filename": media_file.filename,
                "message": "Audio uploaded and transcription started"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/media/files/{file_id}")
    async def get_media_file(file_id: str):
        """Get media file by ID"""
        try:
            # This would return the actual file
            # For now, return file info
            return {"file_id": file_id, "url": f"/media/files/{file_id}"}
        except Exception as e:
            raise HTTPException(status_code=404, detail="File not found")
    
    @app.get("/api/media/list")
    async def list_media_files(
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None
    ):
        """List media files with optional filtering"""
        try:
            files = advanced_media.get_media_files(reference_type, reference_id)
            return {"media_files": files}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== OCR ENDPOINTS ====================
    
    @app.post("/api/ocr/extract-text/{file_id}")
    async def extract_text_from_image(file_id: str):
        """Extract text from uploaded image using OCR"""
        try:
            extracted_text = await advanced_media.extract_text_from_image(file_id)
            
            if extracted_text:
                return {
                    "success": True,
                    "extracted_text": extracted_text,
                    "message": "Text extracted successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "No text found or OCR not available"
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/ocr/upload-and-extract")
    async def upload_image_and_extract_text(
        file: UploadFile = File(...),
        reference_type: str = Form("document"),
        reference_id: int = Form(0)
    ):
        """Upload image and immediately extract text"""
        try:
            # Upload image first
            file_data = await file.read()
            
            media_file = await advanced_media.upload_image(
                image_data=file_data,
                filename=file.filename,
                reference_type=reference_type,
                reference_id=reference_id,
                uploaded_by=1  # Default user
            )
            
            # Extract text
            extracted_text = await advanced_media.extract_text_from_image(media_file.id)
            
            return {
                "success": True,
                "file_id": media_file.id,
                "extracted_text": extracted_text or "",
                "message": "Image uploaded and text extracted"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== SPEECH-TO-TEXT ENDPOINTS ====================
    
    @app.post("/api/speech/transcribe/{file_id}")
    async def get_transcription(file_id: str):
        """Get transcription for audio file"""
        try:
            # Get transcription from database
            conn = advanced_media.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT transcription, confidence_score, language, ai_summary
                FROM speech_transcriptions 
                WHERE media_file_id = ?
                ORDER BY processing_date DESC
                LIMIT 1
            ''', (file_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "success": True,
                    "transcription": result[0],
                    "confidence_score": result[1],
                    "language": result[2],
                    "ai_summary": result[3]
                }
            else:
                return {
                    "success": False,
                    "message": "Transcription not found or still processing"
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/speech/create-work-order")
    async def create_work_order_from_speech(request: Request):
        """Create work order from speech input"""
        try:
            body = await request.json()
            speech_text = body.get("speech_text", "")
            
            if not speech_text:
                raise HTTPException(status_code=400, detail="Speech text required")
            
            # Create work order from speech
            await advanced_media._create_work_order_from_speech(speech_text)
            
            return {
                "success": True,
                "message": "Work order created from speech input"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/speech/start-live-recognition")
    async def start_live_speech_recognition():
        """Start real-time speech recognition"""
        try:
            stop_function = await advanced_media.start_real_time_speech_recognition()
            
            if stop_function:
                return {
                    "success": True,
                    "message": "Real-time speech recognition started",
                    "session_id": "live_speech_session"
                }
            else:
                return {
                    "success": False,
                    "message": "Speech recognition not available"
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== AI ADMIN DASHBOARD ENDPOINTS ====================
    
    @app.get("/api/admin/ai/dashboard")
    async def get_ai_admin_dashboard():
        """Get AI admin dashboard data"""
        try:
            # Get performance summary
            performance = ai_admin.get_model_performance_summary(days=7)
            
            # Get active alerts
            alerts = ai_admin.get_active_alerts()
            
            # Get cost analysis
            costs = ai_admin.get_cost_analysis(days=30)
            
            return {
                "performance_summary": performance,
                "active_alerts": alerts,
                "cost_analysis": costs,
                "dashboard_generated": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/admin/ai/models")
    async def list_ai_models():
        """List all configured AI models"""
        try:
            conn = ai_admin.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ai_model_configs ORDER BY created_date DESC')
            
            models = []
            for row in cursor.fetchall():
                models.append({
                    'id': row[0],
                    'model_name': row[1],
                    'model_type': row[2],
                    'endpoint_url': row[3],
                    'is_active': bool(row[6]),
                    'performance_metrics': json.loads(row[7] or "{}"),
                    'last_used': row[8],
                    'created_date': row[9]
                })
            
            conn.close()
            return {"models": models}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/admin/ai/models")
    async def add_ai_model(request: Request):
        """Add new AI model configuration"""
        try:
            body = await request.json()
            
            config_id = await ai_admin.add_model_config(
                model_name=body.get("model_name"),
                model_type=body.get("model_type"),
                endpoint_url=body.get("endpoint_url", ""),
                api_key=body.get("api_key", ""),
                parameters=body.get("parameters", {}),
                user_id=body.get("user_id", 1)
            )
            
            return {
                "success": True,
                "config_id": config_id,
                "message": "AI model configuration added"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/api/admin/ai/models/{config_id}")
    async def update_ai_model(config_id: int, request: Request):
        """Update AI model configuration"""
        try:
            body = await request.json()
            
            success = await ai_admin.update_model_config(config_id, body)
            
            return {
                "success": success,
                "message": "AI model configuration updated" if success else "Update failed"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/admin/ai/models/{model_name}/test")
    async def test_ai_model(model_name: str):
        """Test AI model connection"""
        try:
            result = await ai_admin.test_model_connection(model_name)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/admin/ai/performance/{model_name}")
    async def get_model_performance(model_name: str, days: int = 7):
        """Get detailed performance metrics for a specific model"""
        try:
            # Get from cache first
            if model_name in ai_admin.performance_cache:
                cached_metrics = ai_admin.performance_cache[model_name]
                
                # Get additional database metrics
                conn = ai_admin.get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        DATE(request_timestamp) as date,
                        COUNT(*) as requests,
                        AVG(response_time_ms) as avg_response_time,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests
                    FROM ai_request_logs 
                    WHERE model_name = ? AND request_timestamp >= datetime('now', '-{} days')
                    GROUP BY DATE(request_timestamp)
                    ORDER BY date
                '''.format(days), (model_name,))
                
                daily_metrics = []
                for row in cursor.fetchall():
                    daily_metrics.append({
                        'date': row[0],
                        'requests': row[1],
                        'avg_response_time': row[2],
                        'success_rate': (row[3] / row[1]) if row[1] > 0 else 0
                    })
                
                conn.close()
                
                return {
                    "model_name": model_name,
                    "current_metrics": {
                        "total_requests": cached_metrics.total_requests,
                        "success_rate": (cached_metrics.successful_requests / cached_metrics.total_requests) if cached_metrics.total_requests > 0 else 0,
                        "average_response_time": cached_metrics.average_response_time,
                        "average_confidence": cached_metrics.average_confidence,
                        "total_cost": cached_metrics.total_cost
                    },
                    "daily_metrics": daily_metrics
                }
            else:
                return {
                    "model_name": model_name,
                    "message": "No recent performance data available"
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/admin/ai/alerts")
    async def get_ai_alerts():
        """Get active AI performance alerts"""
        try:
            alerts = ai_admin.get_active_alerts()
            return {"alerts": alerts}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/admin/ai/alerts/{alert_id}/acknowledge")
    async def acknowledge_alert(alert_id: int, request: Request):
        """Acknowledge an AI alert"""
        try:
            body = await request.json()
            user_id = body.get("user_id", 1)
            
            conn = ai_admin.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE ai_alerts 
                SET acknowledged = TRUE, acknowledged_by = ?, acknowledged_date = ?
                WHERE id = ?
            ''', (user_id, datetime.now(), alert_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Alert acknowledged"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== WEB INTERFACE FOR ADVANCED FEATURES ====================
    
    @app.get("/admin/ai-dashboard", response_class=HTMLResponse)
    async def ai_admin_dashboard_page():
        """AI Admin Dashboard web interface"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Admin Dashboard - ChatterFix CMMS</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric { display: flex; justify-content: space-between; margin: 10px 0; }
                .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
                .alert.high { background: #ffebee; border-left: 4px solid #f44336; }
                .alert.medium { background: #fff3e0; border-left: 4px solid #ff9800; }
                .alert.low { background: #e8f5e8; border-left: 4px solid #4caf50; }
            </style>
        </head>
        <body>
            <h1>🤖 AI Admin Dashboard</h1>
            
            <div class="dashboard">
                <div class="card">
                    <h3>📊 Model Performance</h3>
                    <div id="performance-metrics">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>⚠️ Active Alerts</h3>
                    <div id="alerts">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>💰 Cost Analysis</h3>
                    <div id="cost-analysis">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>🔧 Model Management</h3>
                    <div id="model-management">
                        <button onclick="testAllModels()">Test All Models</button>
                        <div id="model-tests"></div>
                    </div>
                </div>
            </div>
            
            <script>
                async function loadDashboard() {
                    try {
                        const response = await fetch('/api/admin/ai/dashboard');
                        const data = await response.json();
                        
                        // Update performance metrics
                        const perfDiv = document.getElementById('performance-metrics');
                        const models = data.performance_summary.model_statistics || {};
                        perfDiv.innerHTML = Object.keys(models).map(model => {
                            const stats = models[model];
                            return `
                                <div class="metric">
                                    <strong>${model}:</strong>
                                    <span>${stats.total_requests} requests (${(stats.success_rate * 100).toFixed(1)}% success)</span>
                                </div>
                            `;
                        }).join('');
                        
                        // Update alerts
                        const alertsDiv = document.getElementById('alerts');
                        const alerts = data.active_alerts || [];
                        alertsDiv.innerHTML = alerts.map(alert => `
                            <div class="alert ${alert.severity}">
                                <strong>${alert.model_name}:</strong> ${alert.message}
                            </div>
                        `).join('') || 'No active alerts';
                        
                        // Update costs
                        const costDiv = document.getElementById('cost-analysis');
                        const costs = data.cost_analysis || {};
                        costDiv.innerHTML = `
                            <div class="metric">
                                <span>Total Cost (30d):</span>
                                <strong>$${(costs.total_cost || 0).toFixed(2)}</strong>
                            </div>
                            <div class="metric">
                                <span>Average Daily:</span>
                                <strong>$${(costs.average_daily_cost || 0).toFixed(2)}</strong>
                            </div>
                        `;
                        
                    } catch (error) {
                        console.error('Dashboard load failed:', error);
                    }
                }
                
                async function testAllModels() {
                    const testDiv = document.getElementById('model-tests');
                    testDiv.innerHTML = 'Testing models...';
                    
                    const models = ['ollama', 'grok', 'openai'];
                    const results = [];
                    
                    for (const model of models) {
                        try {
                            const response = await fetch(`/api/admin/ai/models/${model}/test`, {method: 'POST'});
                            const result = await response.json();
                            results.push(`${model}: ${result.success ? '✅' : '❌'} ${result.message || result.error}`);
                        } catch (error) {
                            results.push(`${model}: ❌ Connection failed`);
                        }
                    }
                    
                    testDiv.innerHTML = results.join('<br>');
                }
                
                // Load dashboard on page load
                loadDashboard();
                
                // Refresh every 30 seconds
                setInterval(loadDashboard, 30000);
            </script>
        </body>
        </html>
        """
    
    print("✅ Advanced feature endpoints added successfully!")

# Export function for main app integration
def setup_advanced_features(app: FastAPI):
    """Setup advanced features in main app"""
    try:
        print("🔧 Setting up advanced features...")
        add_advanced_endpoints(app)
        print("✅ Advanced endpoints added successfully")
        return True
    except Exception as e:
        print(f"❌ Advanced features setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False