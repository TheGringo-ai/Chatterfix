import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_database
from app.routers import dashboard, work_orders, ar, inventory, ai, assets, team, training, feedback, geolocation, planner, purchasing, onboarding, rag
from app.services.ai_assistant import chatterfix_ai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix CMMS",
    description="AI-Powered Maintenance Management System",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include Routers
app.include_router(dashboard.router)
app.include_router(work_orders.router)
app.include_router(ar.router)
app.include_router(inventory.router)
app.include_router(ai.router)
app.include_router(assets.router)
app.include_router(team.router)
app.include_router(training.router)
app.include_router(feedback.router)
app.include_router(geolocation.router)
app.include_router(planner.router)
app.include_router(purchasing.router)
app.include_router(onboarding.router)
app.include_router(rag.router)

@app.on_event("startup")
async def startup_event():
    """Initialize application services on startup"""
    logger.info("🚀 ChatterFix CMMS starting up...")
    
    # Initialize Database
    init_database()
    
    # Initialize AI Services
    await chatterfix_ai.start()
    
    logger.info("✅ Startup complete. Application ready.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CMMS_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
