"""
API routes for the Utility Infrastructure Knowledge Extraction API.

Defines REST endpoints for equipment, locations, maintenance,
search, data upload, and export. Includes basic validation and
error handling.
"""

from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import Dict, Any
import logging
import io
import pandas as pd
import json

from src.data_processor import (
    build_datastore,
    search,
    export_as_json,
    DataStore,
)
from src.models import SearchResults
from src.exceptions import DataUnavailableError

logger = logging.getLogger(__name__)

# Initial datastore with provided files
DATA_CSV = "data/equipment_inventory.csv"
DATA_JSON = "data/maintenance_logs.json"
store: DataStore = build_datastore(DATA_CSV, DATA_JSON)

# Define router (included in main.py)
router = APIRouter(prefix="/api", tags=["API"])


@router.get("/equipment")
def list_equipment() -> Dict[str, Any]:
    """Return all equipment records."""
    if not store.equipment:
        raise DataUnavailableError("Equipment")
    logger.info("Fetching equipment list")
    return {"equipment": store.equipment}


@router.get("/locations")
def list_locations() -> Dict[str, Any]:
    """Return unique equipment locations."""
    if not store.locations:
        raise DataUnavailableError("Location")
    logger.info("Fetching location list")
    return {"locations": store.locations}


@router.get("/maintenance")
def list_maintenance() -> Dict[str, Any]:
    """Return all maintenance logs."""
    if not store.maintenance:
        raise DataUnavailableError("Maintenance")
    logger.info("Fetching maintenance logs")
    return {"maintenance": store.maintenance}


@router.get("/search", response_model=SearchResults)
def search_entities(query: str = Query(..., min_length=1)) -> SearchResults:
    """Search across equipment and maintenance records."""
    q = query.strip()
    results = search(store, q)

    if not results["equipment"] and not results["maintenance"]:
        raise HTTPException(status_code=404, detail="No matches found")

    logger.info("Search requested: %s", q)
    return SearchResults(**results)


@router.post("/process")
async def process_new_data(
    equipment_file: UploadFile = File(...),
    maintenance_file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Upload new data files and rebuild the in-memory datastore."""
    try:
        eq_df = pd.read_csv(io.BytesIO(await equipment_file.read()))
        mt_data = json.loads((await maintenance_file.read()).decode("utf-8"))
        mt_df = pd.DataFrame(mt_data)
    except Exception as e:
        logger.error("Error processing uploaded files: %s", e)
        raise HTTPException(status_code=422, detail="Invalid file format or content")

    global store
    store = DataStore(eq_df, mt_df)

    logger.info("Datastore updated with new uploaded files")
    return {"status": "Data processed successfully"}


@router.get("/export")
def export_data() -> Dict[str, Any]:
    """Export combined equipment with their maintenance logs."""
    if not store.equipment or not store.maintenance:
        raise DataUnavailableError("Export")
    logger.info("Exporting combined data")
    return export_as_json(store)
