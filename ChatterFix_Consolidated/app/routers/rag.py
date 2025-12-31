"""
RAG Router - Document-based training enhancement API
"""

import logging
from typing import Optional
from fastapi import APIRouter, File, Form, Request, UploadFile, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rag", tags=["RAG"])


def get_current_user(request: Request):
    """Get current user from request."""
    # Simplified auth - in production use proper auth
    return type('User', (), {'organization_id': 'demo_org', 'uid': 'demo_user'})()


@router.post("/documents/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
):
    """Upload a document for RAG processing."""
    from app.services.rag import rag_service

    current_user = get_current_user(request)
    try:
        content = await file.read()
        metadata = {}
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = [t.strip() for t in tags.split(",")]

        result = await rag_service.process_and_store_document(
            file_content=content,
            filename=file.filename,
            organization_id=current_user.organization_id,
            mime_type=file.content_type,
            metadata=metadata,
        )

        if result["success"]:
            return JSONResponse(content=result)
        raise HTTPException(status_code=400, detail=result.get("error"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(request: Request, limit: int = 50):
    """List all RAG documents."""
    from app.services.rag import rag_service

    current_user = get_current_user(request)
    try:
        documents = await rag_service.list_documents(current_user.organization_id, limit)
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(request: Request, document_id: str):
    """Delete a document."""
    from app.services.rag import rag_service

    current_user = get_current_user(request)
    try:
        success = await rag_service.delete_document(document_id, current_user.organization_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(request: Request, query: str = Form(...), limit: int = Form(5)):
    """Semantic search across documents."""
    from app.services.rag import rag_service

    current_user = get_current_user(request)
    try:
        results = await rag_service.search_documents(query, current_user.organization_id, limit)
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_question(request: Request, question: str = Form(...)):
    """Answer a question using RAG context."""
    from app.services.rag import rag_service

    current_user = get_current_user(request)
    try:
        return await rag_service.answer_question_with_context(question, current_user.organization_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(request: Request):
    """Get RAG statistics."""
    from app.services.rag import rag_service

    current_user = get_current_user(request)
    try:
        documents = await rag_service.list_documents(current_user.organization_id)
        total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)
        return {
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "indexed_documents": len([d for d in documents if d.get("status") == "indexed"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
