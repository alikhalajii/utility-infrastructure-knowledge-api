"""
Custom exceptions for the Utility Infrastructure Knowledge Extraction API.
"""

from fastapi import HTTPException


class DataUnavailableError(HTTPException):
    """Raised when a requested data resource is unavailable (e.g., empty or not loaded)."""

    def __init__(self, resource: str):
        super().__init__(
            status_code=503,
            detail=f"{resource} data not available"
        )
