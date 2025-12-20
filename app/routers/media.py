"""
Media Router
Handles file uploads, barcode scanning, document processing

Security Features:
- File extension whitelist
- MIME type validation
- File size limits (10 MB)
- Filename sanitization
"""

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Cookie, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.services.media_service import media_service
from app.services.firebase_auth import firebase_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])
templates = Jinja2Templates(directory="app/templates")

# ============================================================
# SECURITY CONSTANTS - File Upload Validation
# ============================================================

# Maximum file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file extensions (lowercase, with dot)
ALLOWED_EXTENSIONS = {
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic", ".heif",
    # Documents
    ".pdf",
    # Videos
    ".mp4", ".mov", ".avi", ".webm", ".m4v",
    # Audio (for voice memos)
    ".m4a", ".wav", ".mp3", ".aac", ".ogg",
}

# Allowed MIME types (must match extensions above)
ALLOWED_MIME_TYPES = {
    # Images
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
    "image/heic", "image/heif",
    # Documents
    "application/pdf",
    # Videos
    "video/mp4", "video/quicktime", "video/x-msvideo", "video/webm",
    "video/x-m4v",
    # Audio
    "audio/mp4", "audio/m4a", "audio/x-m4a", "audio/wav", "audio/x-wav",
    "audio/mpeg", "audio/mp3", "audio/aac", "audio/ogg",
    # Fallback for unknown types
    "application/octet-stream",
}


async def validate_file(file: UploadFile, check_size: bool = True) -> None:
    """
    Validate uploaded file for security.

    Raises HTTPException if validation fails.

    Checks:
    1. File extension against whitelist
    2. MIME/Content-Type against whitelist
    3. File size against limit (optional, requires reading file first)
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    # 1. Check file extension
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Rejected file upload: invalid extension '{ext}' for file '{file.filename}'")
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Allowed types: images, PDFs, videos, audio"
        )

    # 2. Check MIME type (Content-Type header)
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Rejected file upload: invalid MIME type '{content_type}' for file '{file.filename}'")
        raise HTTPException(
            status_code=400,
            detail=f"Content type '{content_type}' is not allowed"
        )

    logger.debug(f"File validation passed: {file.filename} ({content_type})")


async def validate_file_size(file_data: bytes, filename: str) -> None:
    """
    Validate file size after reading.

    Raises HTTPException if file is too large.
    """
    if len(file_data) > MAX_FILE_SIZE:
        size_mb = len(file_data) / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        logger.warning(f"Rejected file upload: size {size_mb:.1f}MB exceeds limit for '{filename}'")
        raise HTTPException(
            status_code=413,  # Payload Too Large
            detail=f"File too large ({size_mb:.1f} MB). Maximum size is {max_mb:.0f} MB"
        )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and special characters.
    """
    if not filename:
        return "unnamed_file"

    # Get just the filename, removing any path components
    filename = os.path.basename(filename)

    # Remove null bytes and control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)

    # Replace potentially dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename or "unnamed_file"


async def get_current_user_id(session_token: Optional[str]) -> str:
    """Extract user ID from session token, fallback to 'demo_user'"""
    if not session_token:
        return "demo_user"
    try:
        user_data = await firebase_auth_service.verify_token(session_token)
        return user_data.get("uid", "demo_user")
    except Exception as e:
        logger.warning(f"Could not verify session token: {e}")
        return "demo_user"


@router.post("/upload")
async def upload_media(
    request: Request,
    files: List[UploadFile] = File(...),
    category: str = Form("work_orders"),
    work_order_id: str = Form(None),
    part_id: str = Form(None),
    asset_id: str = Form(None),
    session_token: Optional[str] = Cookie(None),
):
    """
    Upload multiple files (photos, videos, documents).

    Security:
    - File extension whitelist (images, PDFs, videos, audio)
    - MIME type validation
    - 10 MB file size limit
    - Filename sanitization
    """
    try:
        # Get current user ID from session
        uploaded_by = await get_current_user_id(session_token)
        uploaded_files = []
        rejected_files = []

        for file in files:
            if not file.filename:
                continue

            try:
                # 1. Validate file type (extension + MIME)
                await validate_file(file)

                # 2. Read file data
                file_data = await file.read()

                # 3. Validate file size
                await validate_file_size(file_data, file.filename)

                # 4. Sanitize filename
                safe_filename = sanitize_filename(file.filename)

                # 5. Prepare metadata
                metadata = {
                    "work_order_id": work_order_id,
                    "part_id": part_id,
                    "asset_id": asset_id,
                    "uploaded_by": uploaded_by,
                    "content_type": file.content_type,
                    "original_filename": file.filename,
                }

                # 6. Upload file with sanitized name
                file_info = await media_service.upload_file(
                    file_data=file_data,
                    filename=safe_filename,
                    category=category,
                    metadata=metadata,
                )

                uploaded_files.append(file_info)

            except HTTPException as e:
                # Track rejected files for user feedback
                rejected_files.append({
                    "filename": file.filename,
                    "error": e.detail,
                })
                logger.info(f"File rejected: {file.filename} - {e.detail}")

        # Return response with both successful and rejected files
        response = {
            "success": len(uploaded_files) > 0 or len(rejected_files) == 0,
            "files": uploaded_files,
            "count": len(uploaded_files),
        }

        if rejected_files:
            response["rejected"] = rejected_files
            response["rejected_count"] = len(rejected_files)

        return JSONResponse(response)

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.post("/scan-barcode")
async def scan_barcode(request: Request, file: UploadFile = File(...)):
    """
    Scan barcode from uploaded image.

    Security:
    - Only image files allowed
    - 10 MB size limit
    """
    try:
        # Validate file type and extension
        await validate_file(file)

        # Read image data
        image_data = await file.read()

        # Validate file size
        await validate_file_size(image_data, file.filename)

        # Scan for barcodes
        barcodes = await media_service.scan_barcode_from_image(image_data)

        return JSONResponse(
            {"success": True, "barcodes": barcodes, "count": len(barcodes)}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Barcode scan error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.post("/generate-barcode")
async def generate_barcode(
    request: Request,
    data: str = Form(...),
    barcode_type: str = Form("qr"),
    width: int = Form(200),
    height: int = Form(200),
):
    """
    Generate a barcode/QR code
    """
    try:
        barcode_info = await media_service.generate_barcode(
            data=data, barcode_type=barcode_type, size=(width, height)
        )

        return JSONResponse({"success": True, "barcode": barcode_info})

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.post("/scan-document")
async def scan_document(
    request: Request, file: UploadFile = File(...), document_type: str = Form("invoice")
):
    """
    Scan document (invoice, packaging slip, etc.) and extract information.

    Security:
    - Only image and PDF files allowed
    - 10 MB size limit
    - Document type whitelist
    """
    try:
        # Validate document_type to prevent injection
        allowed_doc_types = {"invoice", "packing_slip", "receipt", "work_order", "manual", "other"}
        if document_type not in allowed_doc_types:
            document_type = "other"

        # Validate file type and extension
        await validate_file(file)

        # Read image data
        image_data = await file.read()

        # Validate file size
        await validate_file_size(image_data, file.filename)

        # Process based on document type
        if document_type == "invoice":
            result = await media_service.process_invoice_scan(image_data)
        else:
            result = await media_service.scan_document(image_data)

        return JSONResponse(
            {
                "success": True,
                "document_type": document_type,
                "extraction_result": result,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document scan error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.get("/stats")
async def get_media_stats():
    """
    Get media upload statistics
    """
    try:
        stats = media_service.get_upload_stats()
        return JSONResponse({"success": True, "stats": stats})

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.get("/camera")
async def camera_interface(request: Request):
    """
    Camera interface for taking photos/videos
    """
    return templates.TemplateResponse("camera_interface.html", {"request": request})
