"""
FastAPI application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from src.api import router
from src.logger import setup_logging
from src.exceptions import DataUnavailableError

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI instance with metadata
app = FastAPI(
    title="Utility Infrastructure Knowledge Extraction API",
    description="A simple barebone FastAPI application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Include all API routes
app.include_router(router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Health/info endpoint at the root."""
    return {
        "message": "Utility Infrastructure Knowledge Extraction API is running.",
        "docs": "http://localhost:8000/docs",
    }


@app.exception_handler(DataUnavailableError)
async def data_unavailable_handler(request: Request, exc: DataUnavailableError):
    """Return consistent JSON for unavailable data errors."""
    logger.warning("DataUnavailableError: %s", exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "hint": "Try uploading new data via /api/process"
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
