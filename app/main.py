"""
Simple FastAPI Backend for Agadah Bot

Serves both API endpoints and static frontend files.
"""
import logging
import json
import asyncio
from typing import AsyncIterator
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.crew import create_activity_crew

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agadah Bot API",
    description="Generate youth workshop activities from Jewish stories",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check / API info"""
    return {
        "name": "Agadah Bot API",
        "version": "2.0.0",
        "status": "healthy",
        "endpoints": {
            "create": "/api/create?input=YOUR_INPUT",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/create")
async def create_activity(input: str):
    """
    Create youth workshop activity with real-time progress via SSE.

    Args:
        input: Hebrew description of desired activity
            Example: "פעילות על אהבת חינם לחטיבה, 40 דקות"

    Returns:
        Server-Sent Events stream with progress updates
    """

    async def generate():
        """Generator for SSE events"""
        try:
            # Send start event
            yield format_sse("start", {"message": "מתחיל ליצור פעילות..."})

            # Create crew
            logger.info(f"Creating activity for input: {input}")
            crew = create_activity_crew()

            # Track progress
            start_time = datetime.now()

            # TODO: Hook into CrewAI's callback system for real-time updates
            # For now, we'll run and return result
            # In future: use crew.stream() or callbacks

            yield format_sse("progress", {
                "agent": "מעבד קלט",
                "message": "אוסף פרטים על הפעילות..."
            })

            # Run crew
            result = crew.kickoff(inputs={"user_input": input})

            yield format_sse("progress", {
                "agent": "חוקר תכנים",
                "message": "מחפש סיפורים ומשחקים..."
            })

            await asyncio.sleep(0.5)  # Allow client to receive

            yield format_sse("progress", {
                "agent": "בונה פעילות",
                "message": "יוצר את תוכנית הפעילות..."
            })

            await asyncio.sleep(0.5)

            yield format_sse("progress", {
                "agent": "מעצב",
                "message": "מסדר את הטקסט..."
            })

            await asyncio.sleep(0.5)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Send completion
            yield format_sse("complete", {
                "output": str(result),
                "duration_seconds": duration
            })

            logger.info(f"Activity created successfully in {duration:.1f}s")

        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            yield format_sse("error", {
                "message": f"שגיאה: {str(e)}"
            })

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


def format_sse(event: str, data: dict) -> str:
    """
    Format Server-Sent Event message.

    Args:
        event: Event type (start, progress, complete, error)
        data: Event data dictionary

    Returns:
        Formatted SSE message string
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# Mount static files (serve web/ directory)
app.mount("/", StaticFiles(directory="web", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
