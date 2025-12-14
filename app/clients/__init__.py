"""
HTTP Clients for ChatterFix Microservices
"""

from .ocr_client import (
    OCRHTTPClient,
    get_ocr_client,
    extract_text_tesseract,
    extract_text_easyocr,
    scan_qr_codes,
    check_ocr_health,
)

__all__ = [
    "OCRHTTPClient",
    "get_ocr_client",
    "extract_text_tesseract",
    "extract_text_easyocr",
    "scan_qr_codes",
    "check_ocr_health",
]
