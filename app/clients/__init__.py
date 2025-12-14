"""
HTTP Clients for ChatterFix Microservices

Services:
- OCR Service: Document scanning, QR codes, text extraction
- AI Team Service: Multi-model AI collaboration, autonomous building
"""

from .ocr_client import (
    OCRHTTPClient,
    get_ocr_client,
    extract_text_tesseract,
    extract_text_easyocr,
    scan_qr_codes,
    check_ocr_health,
)

from .ai_team_client import (
    AITeamHTTPClient,
    get_ai_team_client,
    execute_ai_task,
    invoke_autonomous_builder,
    ai_code_review,
    check_ai_team_health,
)

__all__ = [
    # OCR Service
    "OCRHTTPClient",
    "get_ocr_client",
    "extract_text_tesseract",
    "extract_text_easyocr",
    "scan_qr_codes",
    "check_ocr_health",
    # AI Team Service
    "AITeamHTTPClient",
    "get_ai_team_client",
    "execute_ai_task",
    "invoke_autonomous_builder",
    "ai_code_review",
    "check_ai_team_health",
]
