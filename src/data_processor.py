"""Data processing logic for the Utility Knowledge API.

Loads equipment CSV + maintenance JSON, validates schema,
provides accessors, search, and export functions.
"""

# mypy: ignore-errors

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any
import json
import pandas as pd
import logging

from src.logger import setup_logging

# Initialize logging once
setup_logging()
logger = logging.getLogger(__name__)

# Minimal required schema
EQUIPMENT_REQUIRED_COLS = {"equipment_id", "equipment_type", "location"}
MAINTENANCE_REQUIRED_KEYS = {
    "log_id",
    "equipment_id",
    "maintenance_type",
    "date",
    "description",
}


@dataclass
class DataStore:
    """In-memory store for equipment and maintenance data."""

    equipment_df: pd.DataFrame
    maintenance_df: pd.DataFrame

    @property
    def locations(self) -> List[str]:
        """Unique list of equipment locations."""
        if self.equipment_df.empty:
            return []
        return sorted(self.equipment_df["location"].dropna().astype(str).unique().tolist())

    @property
    def equipment(self) -> List[Dict[str, Any]]:
        """All equipment records as dictionaries."""
        return [] if self.equipment_df.empty else self.equipment_df.to_dict(orient="records")

    @property
    def maintenance(self) -> List[Dict[str, Any]]:
        """All maintenance records as dictionaries."""
        return [] if self.maintenance_df.empty else self.maintenance_df.to_dict(orient="records")


def load_equipment_csv(path: str) -> pd.DataFrame:
    """Load and validate equipment CSV."""
    df = pd.read_csv(path)
    missing = EQUIPMENT_REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Equipment CSV missing columns: {missing}")
    df["equipment_id"] = df["equipment_id"].astype(str)
    df["equipment_type"] = df["equipment_type"].astype(str)
    df["location"] = df["location"].astype(str)
    return df


def load_maintenance_json(path: str) -> pd.DataFrame:
    """Load and validate maintenance JSON list."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Maintenance JSON must be a list")
    for i, item in enumerate(data):
        missing = MAINTENANCE_REQUIRED_KEYS - set(item.keys())
        if missing:
            raise ValueError(f"Log at index {i} missing keys: {missing}")
    df = pd.DataFrame(data)
    df["equipment_id"] = df["equipment_id"].astype(str)
    df["maintenance_type"] = df["maintenance_type"].astype(str)
    df["description"] = df["description"].fillna("").astype(str)
    return df


def build_datastore(equipment_csv: str, maintenance_json: str) -> DataStore:
    """Load both sources and return a DataStore."""
    logger.info("Loading equipment from %s", equipment_csv)
    eq_df = load_equipment_csv(equipment_csv)
    logger.info("Loading maintenance from %s", maintenance_json)
    mt_df = load_maintenance_json(maintenance_json)
    return DataStore(eq_df, mt_df)


def join_equipment_maintenance(store: DataStore) -> pd.DataFrame:
    """Join maintenance with equipment by equipment_id."""
    if store.equipment_df.empty or store.maintenance_df.empty:
        return pd.DataFrame()
    return store.maintenance_df.merge(store.equipment_df, on="equipment_id", how="left")


def search(store: DataStore, query: str) -> Dict[str, List[Dict[str, Any]]]:
    """Naive substring search across equipment and maintenance."""
    q = query.strip().lower()
    if not q:
        return {"equipment": [], "maintenance": []}

    # Equipment search
    eq = store.equipment_df.copy()
    eq["_search"] = (
        eq["equipment_id"].astype(str)
        + " "
        + eq["equipment_type"].astype(str)
        + " "
        + eq["location"].astype(str)
        + " "
        + eq.get("manufacturer", "").astype(str)
        + " "
        + eq.get("model", "").astype(str)
    ).str.lower()
    eq_matches = eq[eq["_search"].str.contains(q, na=False)].drop(columns=["_search"])

    # Maintenance search
    mt = store.maintenance_df.copy()
    mt["_search"] = (
        mt["log_id"].astype(str)
        + " "
        + mt["equipment_id"].astype(str)
        + " "
        + mt["maintenance_type"].astype(str)
        + " "
        + mt["description"].astype(str)
        + " "
        + mt.get("technician", "").astype(str)
        + " "
        + mt.get("status", "").astype(str)
    ).str.lower()
    mt_matches = mt[mt["_search"].str.contains(q, na=False)].drop(columns=["_search"])

    return {
        "equipment": eq_matches.to_dict(orient="records"),
        "maintenance": mt_matches.to_dict(orient="records"),
    }


def export_as_json(store: DataStore) -> Dict[str, Any]:
    """Export equipment with attached maintenance logs."""
    equipment_map = {rec["equipment_id"]: rec.copy() for rec in store.equipment}
    for rec in equipment_map.values():
        rec["maintenance_logs"] = []
    for log in store.maintenance:
        eid = log.get("equipment_id")
        if eid in equipment_map:
            equipment_map[eid]["maintenance_logs"].append(log)
    return {"equipment": list(equipment_map.values()), "locations": store.locations}
