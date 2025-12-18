"""
ChatterFix OCR/Vision Microservice
Handles OCR, QR scanning, and image processing
"""

import io
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix OCR Service",
    description="OCR and Vision microservice for technician tools",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-load heavy dependencies
_easyocr_reader = None


def get_easyocr():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr

        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    return _easyocr_reader


class OCRResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    method: str


class QRResponse(BaseModel):
    data: str
    type: str


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ocr-service"}


@app.post("/api/v1/ocr/tesseract", response_model=OCRResponse)
async def ocr_tesseract(file: UploadFile = File(...)):
    """Extract text using Tesseract OCR"""
    try:
        import pytesseract

        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        text = pytesseract.image_to_string(image)
        return OCRResponse(text=text.strip(), method="tesseract")
    except Exception as e:
        logger.error(f"Tesseract OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ocr/easyocr", response_model=OCRResponse)
async def ocr_easyocr(file: UploadFile = File(...)):
    """Extract text using EasyOCR (better for handwriting)"""
    try:
        import cv2

        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        reader = get_easyocr()
        results = reader.readtext(image)
        text = " ".join([r[1] for r in results])
        conf = sum([r[2] for r in results]) / len(results) if results else 0
        return OCRResponse(text=text.strip(), confidence=conf, method="easyocr")
    except Exception as e:
        logger.error(f"EasyOCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/qr/scan", response_model=List[QRResponse])
async def scan_qr(file: UploadFile = File(...)):
    """Scan QR codes from image"""
    try:
        import cv2
        from pyzbar import pyzbar

        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        codes = pyzbar.decode(image)
        return [QRResponse(data=c.data.decode("utf-8"), type=c.type) for c in codes]
    except Exception as e:
        logger.error(f"QR scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
