"""
Media Service
Handles file uploads, image/video processing, document scanning, and barcode operations
"""

import os
import uuid
import logging
import base64
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import mimetypes

# Import with error handling
try:
    from PIL import Image, ImageEnhance
    import cv2
    import numpy as np
    IMAGING_AVAILABLE = True
except ImportError:
    Image = None
    ImageEnhance = None
    cv2 = None
    np = None
    IMAGING_AVAILABLE = False

try:
    import qrcode
    from pyzbar import pyzbar
    BARCODE_AVAILABLE = True
except ImportError:
    qrcode = None
    pyzbar = None
    BARCODE_AVAILABLE = False

logger = logging.getLogger(__name__)

class MediaService:
    """Service for handling all media operations"""
    
    def __init__(self):
        self.upload_dir = Path("app/static/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.upload_dir / "work_orders").mkdir(exist_ok=True)
        (self.upload_dir / "parts").mkdir(exist_ok=True)
        (self.upload_dir / "assets").mkdir(exist_ok=True)
        (self.upload_dir / "documents").mkdir(exist_ok=True)
        (self.upload_dir / "invoices").mkdir(exist_ok=True)
        (self.upload_dir / "barcodes").mkdir(exist_ok=True)
        
        # Supported file types
        self.image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.video_types = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'}
        self.document_types = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
        self.allowed_types = self.image_types | self.video_types | self.document_types

    async def upload_file(
        self, 
        file_data: bytes, 
        filename: str, 
        category: str = "work_orders",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Upload a file and return file info
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            category: Upload category (work_orders, parts, assets, documents, etc.)
            metadata: Additional metadata for the file
            
        Returns:
            Dict with file info including path, URL, type, etc.
        """
        try:
            # Generate unique filename
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.allowed_types:
                raise ValueError(f"File type {file_ext} not allowed")
            
            unique_id = str(uuid.uuid4())
            safe_filename = f"{unique_id}{file_ext}"
            
            # Determine upload path
            upload_path = self.upload_dir / category / safe_filename
            
            # Save file
            with open(upload_path, 'wb') as f:
                f.write(file_data)
            
            # Determine file type
            file_type = self._get_file_type(file_ext)
            
            # Process file based on type
            processed_info = {}
            if file_type == "image" and IMAGING_AVAILABLE:
                processed_info = await self._process_image(upload_path)
            elif file_type == "video":
                processed_info = await self._process_video(upload_path)
            
            # Create file record
            file_info = {
                "id": unique_id,
                "original_name": filename,
                "safe_name": safe_filename,
                "file_path": str(upload_path),
                "url": f"/static/uploads/{category}/{safe_filename}",
                "file_type": file_type,
                "file_ext": file_ext,
                "category": category,
                "size_bytes": len(file_data),
                "uploaded_at": datetime.now().isoformat(),
                "metadata": metadata or {},
                **processed_info
            }
            
            logger.info(f"Uploaded file: {filename} -> {safe_filename}")
            return file_info
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            raise Exception(f"Upload failed: {str(e)}")

    async def _process_image(self, image_path: Path) -> Dict[str, Any]:
        """Process uploaded image - resize, extract metadata, etc."""
        try:
            info = {}
            with Image.open(image_path) as img:
                info["dimensions"] = f"{img.width}x{img.height}"
                info["mode"] = img.mode
                
                # Create thumbnail
                thumbnail_path = image_path.parent / f"thumb_{image_path.name}"
                img.thumbnail((300, 300))
                img.save(thumbnail_path)
                info["thumbnail_url"] = f"/static/uploads/{image_path.parent.name}/thumb_{image_path.name}"
                
                # Try to extract EXIF data
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    info["exif"] = {k: str(v) for k, v in exif.items() if k in [271, 272, 306]}  # Camera make, model, datetime
            
            return info
        except Exception as e:
            logger.warning(f"Image processing error: {e}")
            return {}

    async def _process_video(self, video_path: Path) -> Dict[str, Any]:
        """Process uploaded video - extract metadata, create thumbnail"""
        try:
            info = {}
            if cv2:
                cap = cv2.VideoCapture(str(video_path))
                if cap.isOpened():
                    # Get video properties
                    info["duration"] = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
                    info["fps"] = cap.get(cv2.CAP_PROP_FPS)
                    info["dimensions"] = f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
                    
                    # Create thumbnail from first frame
                    ret, frame = cap.read()
                    if ret:
                        thumbnail_path = video_path.parent / f"thumb_{video_path.stem}.jpg"
                        cv2.imwrite(str(thumbnail_path), frame)
                        info["thumbnail_url"] = f"/static/uploads/{video_path.parent.name}/thumb_{video_path.stem}.jpg"
                    
                cap.release()
            
            return info
        except Exception as e:
            logger.warning(f"Video processing error: {e}")
            return {}

    def _get_file_type(self, file_ext: str) -> str:
        """Determine file type category"""
        if file_ext in self.image_types:
            return "image"
        elif file_ext in self.video_types:
            return "video"
        elif file_ext in self.document_types:
            return "document"
        return "unknown"

    async def scan_barcode_from_image(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Scan barcodes/QR codes from image data
        
        Returns:
            List of detected barcodes with their data and positions
        """
        if not BARCODE_AVAILABLE:
            raise Exception("Barcode scanning not available - install pyzbar")
        
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Scan for barcodes
            barcodes = pyzbar.decode(image)
            
            results = []
            for barcode in barcodes:
                # Extract barcode data
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                
                # Get position
                points = barcode.polygon
                if len(points) == 4:
                    rect = {
                        "x": min(p.x for p in points),
                        "y": min(p.y for p in points),
                        "width": max(p.x for p in points) - min(p.x for p in points),
                        "height": max(p.y for p in points) - min(p.y for p in points)
                    }
                else:
                    rect = barcode.rect._asdict()
                
                results.append({
                    "data": barcode_data,
                    "type": barcode_type,
                    "position": rect,
                    "confidence": 1.0  # pyzbar doesn't provide confidence
                })
            
            logger.info(f"Found {len(results)} barcodes in image")
            return results
            
        except Exception as e:
            logger.error(f"Barcode scanning error: {e}")
            raise Exception(f"Barcode scan failed: {str(e)}")

    async def generate_barcode(
        self, 
        data: str, 
        barcode_type: str = "qr",
        size: tuple = (200, 200)
    ) -> Dict[str, Any]:
        """
        Generate a barcode/QR code
        
        Args:
            data: Data to encode
            barcode_type: Type of barcode (qr, code128, etc.)
            size: Size of generated barcode
            
        Returns:
            Dict with barcode info and file path
        """
        if not BARCODE_AVAILABLE:
            raise Exception("Barcode generation not available - install qrcode")
        
        try:
            # Generate unique filename
            barcode_id = str(uuid.uuid4())
            filename = f"barcode_{barcode_id}.png"
            file_path = self.upload_dir / "barcodes" / filename
            
            if barcode_type.lower() == "qr":
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                img = img.resize(size)
                img.save(file_path)
            else:
                # For other barcode types, would need python-barcode library
                raise Exception(f"Barcode type {barcode_type} not implemented yet")
            
            return {
                "id": barcode_id,
                "data": data,
                "type": barcode_type,
                "file_path": str(file_path),
                "url": f"/static/uploads/barcodes/{filename}",
                "size": size,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Barcode generation error: {e}")
            raise Exception(f"Barcode generation failed: {str(e)}")

    async def scan_document(self, image_data: bytes) -> Dict[str, Any]:
        """
        Scan document image and extract text using OCR
        
        Returns:
            Dict with extracted text and confidence
        """
        # This would require pytesseract or similar OCR library
        # For now, return placeholder
        return {
            "text": "OCR functionality requires pytesseract library",
            "confidence": 0.0,
            "processed": False,
            "note": "Install pytesseract to enable document scanning"
        }

    async def process_invoice_scan(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process scanned invoice and extract key information
        
        Returns:
            Dict with extracted invoice data
        """
        # First scan for barcodes
        barcodes = await self.scan_barcode_from_image(image_data)
        
        # Then try OCR (placeholder for now)
        ocr_result = await self.scan_document(image_data)
        
        return {
            "barcodes": barcodes,
            "text_extraction": ocr_result,
            "processed_at": datetime.now().isoformat(),
            "suggested_fields": {
                "invoice_number": None,
                "vendor": None,
                "total": None,
                "date": None,
                "items": []
            }
        }

    def get_upload_stats(self) -> Dict[str, Any]:
        """Get statistics about uploaded files"""
        stats = {
            "total_files": 0,
            "total_size_mb": 0,
            "by_category": {},
            "by_type": {"image": 0, "video": 0, "document": 0}
        }
        
        try:
            for category_dir in self.upload_dir.iterdir():
                if category_dir.is_dir():
                    category_files = list(category_dir.glob("*"))
                    category_size = sum(f.stat().st_size for f in category_files if f.is_file())
                    
                    stats["by_category"][category_dir.name] = {
                        "count": len(category_files),
                        "size_mb": round(category_size / (1024 * 1024), 2)
                    }
                    
                    stats["total_files"] += len(category_files)
                    stats["total_size_mb"] += category_size / (1024 * 1024)
                    
                    # Count by type
                    for file in category_files:
                        if file.is_file():
                            file_type = self._get_file_type(file.suffix.lower())
                            if file_type in stats["by_type"]:
                                stats["by_type"][file_type] += 1
            
            stats["total_size_mb"] = round(stats["total_size_mb"], 2)
            
        except Exception as e:
            logger.error(f"Error getting upload stats: {e}")
        
        return stats

# Global media service instance
media_service = MediaService()