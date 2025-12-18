"""
HTTP Client for OCR Service
Handles communication with the OCR microservice
"""

import logging
import os
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class OCRHTTPClient:
    """HTTP client for communicating with the OCR Service"""

    def __init__(self):
        self.base_url = os.getenv("OCR_SERVICE_URL", "http://localhost:8081").rstrip(
            "/"
        )
        self.timeout = httpx.Timeout(60.0)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        logger.info(f"OCR HTTP client initialized: {self.base_url}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def health_check(self) -> bool:
        """Check OCR service health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json().get("status") == "healthy"
        except Exception as e:
            logger.error(f"OCR health check failed: {e}")
            return False

    async def extract_text_tesseract(self, image_data: bytes) -> dict:
        """Extract text using Tesseract OCR"""
        try:
            files = {"file": ("image.jpg", image_data, "image/jpeg")}
            response = await self.client.post(
                f"{self.base_url}/api/v1/ocr/tesseract", files=files
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return {"text": "", "error": str(e)}

    async def extract_text_easyocr(self, image_data: bytes) -> dict:
        """Extract text using EasyOCR"""
        try:
            files = {"file": ("image.jpg", image_data, "image/jpeg")}
            response = await self.client.post(
                f"{self.base_url}/api/v1/ocr/easyocr", files=files
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return {"text": "", "error": str(e)}

    async def scan_qr_codes(self, image_data: bytes) -> list:
        """Scan QR codes from image"""
        try:
            files = {"file": ("image.jpg", image_data, "image/jpeg")}
            response = await self.client.post(
                f"{self.base_url}/api/v1/qr/scan", files=files
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"QR scan failed: {e}")
            return []


_ocr_client: Optional[OCRHTTPClient] = None


async def get_ocr_client() -> OCRHTTPClient:
    """Get or create OCR HTTP client instance"""
    global _ocr_client
    if _ocr_client is None:
        _ocr_client = OCRHTTPClient()
    return _ocr_client


async def extract_text_tesseract(image_data: bytes) -> dict:
    """Convenience function for Tesseract OCR"""
    client = await get_ocr_client()
    return await client.extract_text_tesseract(image_data)


async def extract_text_easyocr(image_data: bytes) -> dict:
    """Convenience function for EasyOCR"""
    client = await get_ocr_client()
    return await client.extract_text_easyocr(image_data)


async def scan_qr_codes(image_data: bytes) -> list:
    """Convenience function for QR scanning"""
    client = await get_ocr_client()
    return await client.scan_qr_codes(image_data)


async def check_ocr_health() -> bool:
    """Check if OCR service is available"""
    try:
        client = await get_ocr_client()
        return await client.health_check()
    except Exception:
        return False
