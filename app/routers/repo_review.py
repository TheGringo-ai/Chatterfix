"""
Repository Review Router - Web UI for GitHub repository analysis.

Provides a simple web interface for analyzing public GitHub repositories
using the repo-review tool. Returns Markdown reports with security,
dependency, and code quality findings.
"""

import asyncio
import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

# Add tools/repo-review to Python path for imports
REPO_REVIEW_PATH = Path(__file__).parent.parent.parent / "tools" / "repo-review"
if str(REPO_REVIEW_PATH) not in sys.path:
    sys.path.insert(0, str(REPO_REVIEW_PATH))

# Import repo-review modules
try:
    from cloner import clone_repo, cleanup_repo, validate_github_url
    from detector import detect_stack
    from analyzers import run_all_analyzers
    from reporter import generate_report
    REPO_REVIEW_AVAILABLE = True
except ImportError as e:
    REPO_REVIEW_AVAILABLE = False
    IMPORT_ERROR = str(e)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools/repo-review", tags=["Tools"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def repo_review_page(request: Request):
    """Render the repo-review web UI page."""
    return templates.TemplateResponse(
        "tools/repo_review.html",
        {
            "request": request,
            "user": None,
            "current_user": None,
            "is_demo": True,
        },
    )


@router.post("/analyze", response_class=PlainTextResponse)
async def analyze_repository(
    repo_url: str = Form(...),
) -> PlainTextResponse:
    """
    Analyze a public GitHub repository and return a Markdown report.

    Args:
        repo_url: The GitHub repository URL to analyze

    Returns:
        PlainTextResponse with Markdown report
    """
    # Check if repo-review module is available
    if not REPO_REVIEW_AVAILABLE:
        logger.error(f"repo-review module not available: {IMPORT_ERROR}")
        raise HTTPException(
            status_code=500,
            detail=f"Repository review tool not available: {IMPORT_ERROR}",
        )

    # Validate GitHub URL before processing
    if not validate_github_url(repo_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Please provide a valid public GitHub repository URL (e.g., https://github.com/owner/repo).",
        )

    clone_path = None

    try:
        # Clone repository (blocking operation - run in thread)
        logger.info(f"Cloning repository: {repo_url}")
        clone_path = await asyncio.to_thread(clone_repo, repo_url, False)

        if not clone_path:
            raise HTTPException(
                status_code=400,
                detail="Failed to clone repository. Please ensure it is a valid public GitHub repository.",
            )

        # Detect stack (blocking operation - run in thread)
        logger.info(f"Detecting stack for: {clone_path}")
        stack_info = await asyncio.to_thread(detect_stack, str(clone_path))

        # Run all analyzers (blocking operation - run in thread)
        logger.info(f"Running analyzers on: {clone_path}")
        analysis_results = await asyncio.to_thread(
            run_all_analyzers,
            str(clone_path),
            stack_info,
            False,  # verbose=False
        )

        # Generate report (no AI analysis for speed on web)
        logger.info("Generating report")
        report = await asyncio.to_thread(
            generate_report,
            repo_url,
            stack_info,
            analysis_results,
            None,  # ai_insights=None (skip AI for speed)
        )

        return PlainTextResponse(
            content=report,
            media_type="text/markdown",
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )
    finally:
        # Always cleanup cloned repo
        if clone_path:
            try:
                await asyncio.to_thread(cleanup_repo, clone_path)
                logger.info(f"Cleaned up: {clone_path}")
            except Exception as cleanup_error:
                logger.warning(f"Cleanup failed: {cleanup_error}")


@router.get("/health")
async def repo_review_health():
    """Check repo-review service health."""
    return {
        "healthy": REPO_REVIEW_AVAILABLE,
        "status": "operational" if REPO_REVIEW_AVAILABLE else "unavailable",
        "error": None if REPO_REVIEW_AVAILABLE else IMPORT_ERROR,
    }
