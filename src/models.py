from pydantic import BaseModel
from typing import Any, Dict, List


class Equipment(BaseModel):
    equipment_id: str
    equipment_type: str
    location: str
    manufacturer: str | None = None
    model: str | None = None


class Maintenance(BaseModel):
    log_id: str
    equipment_id: str
    maintenance_type: str
    date: str
    description: str
    technician: str | None = None
    status: str | None = None


class SearchResults(BaseModel):
    equipment: List[Dict[str, Any]]
    maintenance: List[Dict[str, Any]]
