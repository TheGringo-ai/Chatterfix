#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Advanced Media & AI Management System
Features: Image Upload, Speech-to-Text, OCR, AI Model Management
"""

import os
import uuid
import base64
import sqlite3
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import hashlib
import asyncio
import logging
from dataclasses import dataclass
import json

# External libraries for advanced features
try:
    import speech_recognition as sr
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
    import whisper
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    print("⚠️  Advanced features require: pip install SpeechRecognition opencv-python pillow pytesseract openai-whisper")

@dataclass
class MediaFile:
    id: str
    filename: str
    file_path: str
    file_type: str
    file_size: int
    upload_date: datetime
    uploaded_by: int
    reference_type: str  # 'work_order', 'asset', 'part'
    reference_id: int
    metadata: Dict[str, Any]

class AdvancedMediaSystem:
    """Advanced media management with AI capabilities"""
    
    def __init__(self, db_path: str = "./data/cmms_enhanced.db", media_dir: str = "./media"):
        self.db_path = db_path
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.media_dir / "images").mkdir(exist_ok=True)
        (self.media_dir / "documents").mkdir(exist_ok=True)
        (self.media_dir / "audio").mkdir(exist_ok=True)
        (self.media_dir / "thumbnails").mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI models if available
        if ADVANCED_FEATURES_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
                self.speech_recognizer = sr.Recognizer()
                self.logger.info("✅ Advanced AI features loaded")
            except Exception as e:
                self.logger.warning(f"⚠️  Some AI features failed to load: {e}")
        
        # Supported file types
        self.supported_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        self.supported_document_types = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
        self.supported_audio_types = {'.wav', '.mp3', '.m4a', '.ogg', '.flac'}
        
        self._init_media_tables()
    
    def _init_media_tables(self):
        """Initialize media-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Media files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_files (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type TEXT,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                uploaded_by INTEGER,
                reference_type TEXT,
                reference_id INTEGER,
                metadata TEXT DEFAULT '{}',
                thumbnail_path TEXT,
                processed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        ''')
        
        # OCR results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ocr_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_file_id TEXT NOT NULL,
                extracted_text TEXT,
                confidence_score DECIMAL(3,2),
                language TEXT DEFAULT 'en',
                processing_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                ai_analysis TEXT,
                FOREIGN KEY (media_file_id) REFERENCES media_files (id)
            )
        ''')
        
        # Speech transcription table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS speech_transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_file_id TEXT NOT NULL,
                transcription TEXT NOT NULL,
                confidence_score DECIMAL(3,2),
                language TEXT DEFAULT 'en',
                processing_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                speaker_identification TEXT,
                ai_summary TEXT,
                FOREIGN KEY (media_file_id) REFERENCES media_files (id)
            )
        ''')
        
        # AI model configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_model_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL, -- 'ollama', 'openai', 'grok'
                endpoint_url TEXT,
                api_key TEXT,
                model_parameters TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                performance_metrics TEXT DEFAULT '{}',
                last_used DATETIME,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== IMAGE MANAGEMENT ====================
    
    async def upload_image(self, image_data: bytes, filename: str, reference_type: str, 
                          reference_id: int, uploaded_by: int, metadata: Dict = None) -> MediaFile:
        """Upload and process an image file"""
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in self.supported_image_types:
                raise ValueError(f"Unsupported image type: {file_ext}")
            
            # Save original image
            file_path = self.media_dir / "images" / f"{file_id}{file_ext}"
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(file_path, file_id)
            
            # Extract image metadata
            image_metadata = self._extract_image_metadata(file_path)
            if metadata:
                image_metadata.update(metadata)
            
            # Save to database
            media_file = MediaFile(
                id=file_id,
                filename=f"{file_id}{file_ext}",
                file_path=str(file_path),
                file_type='image',
                file_size=len(image_data),
                upload_date=datetime.now(),
                uploaded_by=uploaded_by,
                reference_type=reference_type,
                reference_id=reference_id,
                metadata=image_metadata
            )
            
            self._save_media_file(media_file, thumbnail_path)
            
            # Process with AI if available
            if ADVANCED_FEATURES_AVAILABLE:
                await self._analyze_image_with_ai(media_file)
            
            return media_file
            
        except Exception as e:
            self.logger.error(f"Image upload failed: {e}")
            raise
    
    async def _generate_thumbnail(self, image_path: Path, file_id: str) -> str:
        """Generate thumbnail for image"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE:
                return ""
            
            with Image.open(image_path) as img:
                # Create thumbnail
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                thumbnail_path = self.media_dir / "thumbnails" / f"{file_id}_thumb.jpg"
                img.save(thumbnail_path, "JPEG", quality=85)
                
                return str(thumbnail_path)
                
        except Exception as e:
            self.logger.error(f"Thumbnail generation failed: {e}")
            return ""
    
    def _extract_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Extract metadata from image"""
        metadata = {}
        try:
            if ADVANCED_FEATURES_AVAILABLE:
                with Image.open(image_path) as img:
                    metadata = {
                        'width': img.width,
                        'height': img.height,
                        'format': img.format,
                        'mode': img.mode,
                        'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                    }
                    
                    # Extract EXIF data if available
                    if hasattr(img, '_getexif') and img._getexif():
                        exif = img._getexif()
                        if exif:
                            metadata['exif'] = {str(k): str(v) for k, v in exif.items()}
        except Exception as e:
            self.logger.warning(f"Metadata extraction failed: {e}")
        
        return metadata
    
    async def _analyze_image_with_ai(self, media_file: MediaFile):
        """Analyze image content with AI"""
        try:
            # This would integrate with vision models
            # For now, we'll use OCR if text is detected
            if media_file.file_type == 'image':
                await self.extract_text_from_image(media_file.id)
                
        except Exception as e:
            self.logger.error(f"AI image analysis failed: {e}")
    
    # ==================== OCR FUNCTIONALITY ====================
    
    async def extract_text_from_image(self, media_file_id: str) -> Optional[str]:
        """Extract text from image using OCR"""
        if not ADVANCED_FEATURES_AVAILABLE:
            return None
            
        try:
            # Get media file info
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (media_file_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            file_path = result[0]
            
            # Perform OCR
            image = cv2.imread(file_path)
            
            # Preprocess image for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # Extract text
            text = pytesseract.image_to_string(gray)
            confidence = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in confidence['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Save OCR results
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ocr_results (media_file_id, extracted_text, confidence_score, language)
                VALUES (?, ?, ?, ?)
            ''', (media_file_id, text, avg_confidence / 100, 'en'))
            conn.commit()
            conn.close()
            
            # Analyze text with AI
            if text.strip():
                await self._analyze_extracted_text(media_file_id, text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"OCR processing failed: {e}")
            return None
    
    async def _analyze_extracted_text(self, media_file_id: str, text: str):
        """Analyze extracted text with AI for maintenance insights"""
        try:
            # This would send the text to our AI models for analysis
            # For example: detect error codes, maintenance procedures, part numbers
            pass
        except Exception as e:
            self.logger.error(f"Text analysis failed: {e}")
    
    # ==================== SPEECH-TO-TEXT ====================
    
    async def upload_audio_for_transcription(self, audio_data: bytes, filename: str, 
                                           reference_type: str, reference_id: int, 
                                           uploaded_by: int) -> MediaFile:
        """Upload audio file and transcribe it"""
        try:
            file_id = str(uuid.uuid4())
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in self.supported_audio_types:
                raise ValueError(f"Unsupported audio type: {file_ext}")
            
            # Save audio file
            file_path = self.media_dir / "audio" / f"{file_id}{file_ext}"
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            # Create media file record
            media_file = MediaFile(
                id=file_id,
                filename=f"{file_id}{file_ext}",
                file_path=str(file_path),
                file_type='audio',
                file_size=len(audio_data),
                upload_date=datetime.now(),
                uploaded_by=uploaded_by,
                reference_type=reference_type,
                reference_id=reference_id,
                metadata={}
            )
            
            self._save_media_file(media_file)
            
            # Transcribe audio
            if ADVANCED_FEATURES_AVAILABLE:
                await self._transcribe_audio(media_file)
            
            return media_file
            
        except Exception as e:
            self.logger.error(f"Audio upload failed: {e}")
            raise
    
    async def _transcribe_audio(self, media_file: MediaFile):
        """Transcribe audio to text using Whisper"""
        if not ADVANCED_FEATURES_AVAILABLE:
            return
            
        try:
            # Use Whisper for transcription
            result = self.whisper_model.transcribe(media_file.file_path)
            transcription = result['text']
            language = result['language']
            
            # Calculate confidence (Whisper doesn't provide word-level confidence)
            confidence = 0.85  # Whisper generally has high accuracy
            
            # Save transcription
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO speech_transcriptions 
                (media_file_id, transcription, confidence_score, language)
                VALUES (?, ?, ?, ?)
            ''', (media_file.id, transcription, confidence, language))
            conn.commit()
            conn.close()
            
            # Process transcription for work order creation
            await self._process_transcription_for_work_order(media_file.id, transcription)
            
        except Exception as e:
            self.logger.error(f"Audio transcription failed: {e}")
    
    async def _process_transcription_for_work_order(self, media_file_id: str, transcription: str):
        """Process transcription to extract work order information"""
        try:
            # This would use our AI models to extract:
            # - Asset information
            # - Problem description
            # - Priority level
            # - Required actions
            
            # For now, we'll create a basic work order from the transcription
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate work order from speech
            wo_number = f"VO-{datetime.now().strftime('%Y%m%d')}-{media_file_id[:8]}"
            
            cursor.execute('''
                INSERT INTO work_orders (wo_number, title, description, work_type, status, ai_generated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                wo_number,
                "Voice-Generated Work Order",
                f"Auto-generated from voice input: {transcription}",
                "Voice Request",
                "Open",
                True
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Work order generation from speech failed: {e}")
    
    # ==================== REAL-TIME SPEECH ====================
    
    async def start_real_time_speech_recognition(self, callback_function=None):
        """Start real-time speech recognition for live work order creation"""
        if not ADVANCED_FEATURES_AVAILABLE:
            return
            
        try:
            microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with microphone as source:
                self.speech_recognizer.adjust_for_ambient_noise(source)
            
            # Start listening
            def listen_callback(recognizer, audio):
                try:
                    # Recognize speech
                    text = recognizer.recognize_google(audio)
                    
                    # Process the speech input
                    if callback_function:
                        callback_function(text)
                    else:
                        # Default: create work order from speech
                        asyncio.create_task(self._create_work_order_from_speech(text))
                        
                except sr.UnknownValueError:
                    pass  # Speech was unclear
                except sr.RequestError as e:
                    self.logger.error(f"Speech recognition error: {e}")
            
            # Start background listening
            stop_listening = self.speech_recognizer.listen_in_background(microphone, listen_callback)
            
            return stop_listening
            
        except Exception as e:
            self.logger.error(f"Real-time speech recognition failed: {e}")
            return None
    
    async def _create_work_order_from_speech(self, speech_text: str):
        """Create work order from real-time speech input"""
        try:
            # Use AI to parse the speech and extract work order details
            # This would integrate with our multi-AI system
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            wo_number = f"VR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            cursor.execute('''
                INSERT INTO work_orders (wo_number, title, description, work_type, status, ai_generated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                wo_number,
                "Voice Request",
                f"Real-time voice input: {speech_text}",
                "Voice Request",
                "Open",
                True
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Work order created from speech: {wo_number}")
            
        except Exception as e:
            self.logger.error(f"Speech-to-work-order failed: {e}")
    
    # ==================== HELPER FUNCTIONS ====================
    
    def _save_media_file(self, media_file: MediaFile, thumbnail_path: str = ""):
        """Save media file record to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO media_files (
                id, filename, original_filename, file_path, file_type, file_size,
                uploaded_by, reference_type, reference_id, metadata, thumbnail_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            media_file.id,
            media_file.filename,
            media_file.filename,  # Would store original filename separately
            media_file.file_path,
            media_file.file_type,
            media_file.file_size,
            media_file.uploaded_by,
            media_file.reference_type,
            media_file.reference_id,
            json.dumps(media_file.metadata),
            thumbnail_path
        ))
        
        conn.commit()
        conn.close()
    
    def get_media_files(self, reference_type: str = None, reference_id: int = None) -> List[Dict]:
        """Get media files with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM media_files WHERE 1=1"
        params = []
        
        if reference_type:
            query += " AND reference_type = ?"
            params.append(reference_type)
        
        if reference_id:
            query += " AND reference_id = ?"
            params.append(reference_id)
        
        query += " ORDER BY upload_date DESC"
        
        cursor.execute(query, params)
        results = []
        
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'filename': row[1],
                'file_type': row[4],
                'file_size': row[5],
                'upload_date': row[7],
                'reference_type': row[9],
                'reference_id': row[10],
                'thumbnail_path': row[12]
            })
        
        conn.close()
        return results
    
    def get_file_url(self, file_id: str) -> Optional[str]:
        """Get URL for accessing a media file"""
        # This would return a URL for the web interface
        return f"/api/media/files/{file_id}"
    
    def cleanup_old_files(self, days_old: int = 90):
        """Clean up old media files"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find old files
            cursor.execute('''
                SELECT id, file_path, thumbnail_path 
                FROM media_files 
                WHERE upload_date < datetime('now', '-{} days')
            '''.format(days_old))
            
            old_files = cursor.fetchall()
            
            for file_record in old_files:
                file_id, file_path, thumbnail_path = file_record
                
                # Delete physical files
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                except OSError:
                    pass
                
                # Delete database records
                cursor.execute('DELETE FROM media_files WHERE id = ?', (file_id,))
                cursor.execute('DELETE FROM ocr_results WHERE media_file_id = ?', (file_id,))
                cursor.execute('DELETE FROM speech_transcriptions WHERE media_file_id = ?', (file_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up {len(old_files)} old media files")
            
        except Exception as e:
            self.logger.error(f"File cleanup failed: {e}")

# Initialize the advanced media system
advanced_media = AdvancedMediaSystem()