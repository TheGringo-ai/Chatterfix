"""
Document Processor for RAG
Handles text extraction from various document formats:
- PDF
- DOCX
- Plain text
- CSV
- Images (OCR)
"""

import io
import logging
import mimetypes
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document text extraction and chunking."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def process_document(
        self, file_content: bytes, filename: str, mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document and extract text.

        Returns:
            Dict with extracted_text, chunks, and metadata
        """
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

        try:
            extracted_text = await self._extract_text(file_content, filename, mime_type)
            chunks = self._create_chunks(extracted_text)
            metadata = self._extract_metadata(
                filename, mime_type, len(file_content), extracted_text
            )

            return {
                "success": True,
                "extracted_text": extracted_text,
                "chunks": chunks,
                "metadata": metadata,
                "chunk_count": len(chunks),
            }

        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {e}")
            return {"success": False, "error": str(e), "filename": filename}

    async def _extract_text(self, content: bytes, filename: str, mime_type: str) -> str:
        """Extract text from document based on type."""
        if mime_type == "text/plain":
            return content.decode("utf-8", errors="replace")
        elif mime_type == "text/csv":
            return f"[CSV Data]\n{content.decode('utf-8', errors='replace')}"
        elif mime_type == "application/pdf":
            return await self._extract_from_pdf(content, filename)
        elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            return await self._extract_from_docx(content, filename)
        elif mime_type.startswith("image/"):
            return await self._extract_from_image(content, filename)
        else:
            try:
                return content.decode("utf-8", errors="replace")
            except Exception:
                raise ValueError(f"Unsupported file type: {mime_type}")

    async def _extract_from_pdf(self, content: bytes, filename: str) -> str:
        """Extract text from PDF."""
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = [page.extract_text() or "" for page in pdf_reader.pages]
            return "\n\n".join(text_parts)
        except ImportError:
            return f"[PDF: {filename}] PDF extraction requires PyPDF2"
        except Exception as e:
            return f"[PDF: {filename}] Error: {e}"

    async def _extract_from_docx(self, content: bytes, filename: str) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except ImportError:
            return f"[DOCX: {filename}] DOCX extraction requires python-docx"
        except Exception as e:
            return f"[DOCX: {filename}] Error: {e}"

    async def _extract_from_image(self, content: bytes, filename: str) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            image = Image.open(io.BytesIO(content))
            return f"[OCR: {filename}]\n{pytesseract.image_to_string(image)}"
        except ImportError:
            return f"[Image: {filename}] OCR requires pytesseract"
        except Exception as e:
            return f"[Image: {filename}] Error: {e}"

    def _create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            if end < len(text):
                last_end = max(chunk_text.rfind("."), chunk_text.rfind("!"), chunk_text.rfind("?"))
                if last_end > len(chunk_text) * 0.5:
                    chunk_text = chunk_text[:last_end + 1]
                    end = start + last_end + 1
            chunks.append({"id": len(chunks), "text": chunk_text.strip(), "start_index": start, "end_index": end})
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        return chunks

    def _extract_metadata(self, filename: str, mime_type: str, file_size: int, text: str) -> Dict[str, Any]:
        """Extract metadata from document."""
        return {
            "original_name": filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "text_length": len(text),
        }
