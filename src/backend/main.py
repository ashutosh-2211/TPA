"""
Main FastAPI Application for TPA (Travel Planning Agent)

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Import routers
from api.v1.routes import chat, data, auth

# Import database initialization
from db.base import init_db, close_db

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
    title="TPA - Travel Planning Agent API",
    description="""
    AI-powered travel planning assistant that helps users:
    - Find and compare flights
    - Search for hotels
    - Get travel news and information

    Built with LangGraph, GPT-4o-mini, and LangSmith for observability.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event - Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    logger.info("🚀 Starting TPA API...")
    await init_db()
    logger.info("✅ TPA API ready!")


# Shutdown event - Close database connections and HTTP clients
@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections and HTTP clients on application shutdown"""
    logger.info("🛑 Shutting down TPA API...")
    
    # Close HTTP clients from services
    try:
        from services import flight_service, hotel_service, news_service
        await flight_service.close_http_client()
        await hotel_service.close_http_client()
        await news_service.close_http_client()
        logger.info("✅ HTTP clients closed")
    except Exception as e:
        logger.warning(f"⚠️ Error closing HTTP clients: {e}")
    
    # Close database connections
    await close_db()
    logger.info("✅ TPA API shutdown complete!")


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Health check and API info"""
    return {
        "name": "TPA - Travel Planning Agent API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "langsmith_project": os.getenv("LANGSMITH_PROJECT", "Not configured")
    }


# Health check
@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "openai": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
            "search_api": "✓" if os.getenv("SEARCH_API_KEY") else "✗",
            "langsmith": "✓" if os.getenv("LANGCHAIN_API_KEY") else "✗"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
