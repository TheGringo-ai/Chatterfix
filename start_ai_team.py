#!/usr/bin/env python3
"""
Start AI Team Services
Launches both the gRPC AI Team server and FastAPI web server
"""
import asyncio
import logging
import multiprocessing as mp
import signal
import sys
from concurrent.futures import ProcessPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def start_grpc_server():
    """Start the gRPC AI Team server in a separate process"""
    asyncio.set_event_loop(asyncio.new_event_loop())

    try:
        from ai_team.grpc_server import serve

        logger.info("Starting gRPC AI Team server on port 50051...")
        asyncio.run(serve(port=50051))
    except Exception as e:
        logger.error(f"gRPC server failed: {e}")
        sys.exit(1)


def start_fastapi_server():
    """Start the FastAPI web server"""
    import uvicorn

    try:
        logger.info("Starting FastAPI server on port 8000...")
        uvicorn.run(
            "main:app", host="0.0.0.0", port=8000, reload=False, log_level="info"
        )
    except Exception as e:
        logger.error(f"FastAPI server failed: {e}")
        sys.exit(1)


async def main():
    """Main function to coordinate both servers"""
    logger.info("🚀 Starting ChatterFix AI Team Services...")

    # Start gRPC server in background process
    with ProcessPoolExecutor(max_workers=2) as executor:
        # Start gRPC server
        grpc_future = executor.submit(start_grpc_server)

        # Small delay to let gRPC server start
        await asyncio.sleep(2)

        # Start FastAPI server
        fastapi_future = executor.submit(start_fastapi_server)

        logger.info("✅ Both AI Team services are running!")
        logger.info("🌐 FastAPI Web Interface: http://localhost:8000")
        logger.info("🤖 AI Team Dashboard: http://localhost:8000/ai-team")
        logger.info("🔧 gRPC AI Team Service: localhost:50051")
        logger.info("📊 Health Check: http://localhost:8000/ai-team/health")

        try:
            # Wait for both services
            await asyncio.gather(
                asyncio.wrap_future(grpc_future), asyncio.wrap_future(fastapi_future)
            )
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down AI Team services...")
            grpc_future.cancel()
            fastapi_future.cancel()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Enable multiprocessing on all platforms
    mp.set_start_method("spawn", force=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("AI Team services stopped.")
    except Exception as e:
        logger.error(f"Failed to start AI Team services: {e}")
        sys.exit(1)
