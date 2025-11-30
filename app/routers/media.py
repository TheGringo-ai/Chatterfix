"""
Media Router
Handles file uploads, barcode scanning, document processing
"""

from typing import List
from fastapi import APIRouter, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.media_service import media_service

router = APIRouter(prefix="/media", tags=["media"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/upload")
async def upload_media(
    request: Request,
    files: List[UploadFile] = File(...),
    category: str = Form("work_orders"),
    work_order_id: str = Form(None),
    part_id: str = Form(None),
    asset_id: str = Form(None),
):
    """
    Upload multiple files (photos, videos, documents)
    """
    try:
        uploaded_files = []

        for file in files:
            if file.filename:
                # Read file data
                file_data = await file.read()

                # Prepare metadata
                metadata = {
                    "work_order_id": work_order_id,
                    "part_id": part_id,
                    "asset_id": asset_id,
                    "uploaded_by": "current_user",  # TODO: Get from session
                    "content_type": file.content_type,
                }

                # Upload file
                file_info = await media_service.upload_file(
                    file_data=file_data,
                    filename=file.filename,
                    category=category,
                    metadata=metadata,
                )

                uploaded_files.append(file_info)

        return JSONResponse(
            {"success": True, "files": uploaded_files, "count": len(uploaded_files)}
        )

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.post("/scan-barcode")
async def scan_barcode(request: Request, file: UploadFile = File(...)):
    """
    Scan barcode from uploaded image
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Read image data
        image_data = await file.read()

        # Scan for barcodes
        barcodes = await media_service.scan_barcode_from_image(image_data)

        return JSONResponse(
            {"success": True, "barcodes": barcodes, "count": len(barcodes)}
        )

    except Exception as e:
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
    Scan document (invoice, packaging slip, etc.) and extract information
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Read image data
        image_data = await file.read()

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

    except Exception as e:
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
