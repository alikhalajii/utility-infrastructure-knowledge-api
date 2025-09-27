import pytest
import json
from fastapi.testclient import TestClient

from src.data_processor import (
    load_equipment_csv,
    load_maintenance_json,
    build_datastore,
)
from main import app


class TestDataProcessor:
    """Tests for data processing functionality."""

    def test_load_csv_data(self, tmp_path):
        """Test CSV data loading functionality."""
        good_csv = tmp_path / "equipment.csv"
        good_csv.write_text(
            "equipment_id,equipment_type,location,manufacturer,model\n"
            "EQ101,Router,Station AB,Cisco,ISR4000\n"
        )
        df = load_equipment_csv(str(good_csv))
        # Ensure the dataframe is loaded correctly
        assert not df.empty
        # Ensure required columns exist
        assert set(df.columns) >= {"equipment_id", "equipment_type", "location"}

        # Create a CSV missing required columns
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("id,type\n1,Transformer\n")
        # Ensure ValueError is raised due to missing schema
        with pytest.raises(ValueError):
            load_equipment_csv(str(bad_csv))

    def test_load_json_data(self, tmp_path):
        """Test JSON data loading functionality."""
        # Create valid maintenance log JSON with required keys
        valid_data = [
            {
                "log_id": "LOG101",
                "equipment_id": "EQ101",
                "maintenance_type": "Inspection",
                "date": "2024-01-01",
                "description": "Routine check",
                "technician": "Alberto",
                "status": "Completed",
            }
        ]
        good_json = tmp_path / "logs.json"
        good_json.write_text(json.dumps(valid_data))
        df = load_maintenance_json(str(good_json))
        # Ensure the dataframe is loaded correctly
        assert not df.empty
        # Ensure required maintenance fields exist
        assert set(df.columns) >= {"log_id", "equipment_id", "maintenance_type", "date", "description"}

        # Create invalid JSON missing required keys
        bad_data = [{"log_id": "1", "equipment_id": "EQ101"}]
        bad_json = tmp_path / "bad.json"
        bad_json.write_text(json.dumps(bad_data))
        # Ensure ValueError is raised due to missing keys
        with pytest.raises(ValueError):
            load_maintenance_json(str(bad_json))

    def test_extract_entities(self, tmp_path):
        """Test entity extraction via datastore."""
        # Create a minimal valid equipment CSV
        csv_file = tmp_path / "equipment.csv"
        csv_file.write_text(
            "equipment_id,equipment_type,location\n"
            "EQ101,Router,Station AB\n"
        )

        # Create a minimal valid maintenance JSON
        json_file = tmp_path / "logs.json"
        json_file.write_text(
            '[{"log_id":"LOG102","equipment_id":"EQ101","maintenance_type":"Inspection",'
            '"date":"2024-01-01","description":"Routine check"}]'
        )

        # Build datastore from the test files
        store = build_datastore(str(csv_file), str(json_file))

        # Ensure entities are extracted
        assert store.equipment, "Equipment list should not be empty"
        assert store.maintenance, "Maintenance list should not be empty"
        assert "Station AB" in store.locations, "Location should be extracted correctly"


class TestAPI:
    """Tests for API endpoints."""
    client = TestClient(app)

    def test_get_equipment_endpoint(self):
        """Test equipment listing endpoint."""
        response = self.client.get("/api/equipment")

        # The endpoint should always return JSON with an "equipment" key
        assert "equipment" in response.json()

        # Status code depends on whether data is available (200) or not (503)
        assert response.status_code in (200, 503)

    def test_search_endpoint(self):
        """Test search functionality."""
        response = self.client.get("/api/search", params={"query": "Router"})

        # Status code is 200 if matches found, 404 if no matches
        assert response.status_code in (200, 404)

        if response.status_code == 200:
            data = response.json()
            # Ensure both equipment and maintenance keys are always present
            assert "equipment" in data
            assert "maintenance" in data

    def test_export_endpoint(self):
        """Test export endpoint returns nested equipment-maintenance structure or 503."""
        response = self.client.get("/api/export")

        # Status code is 200 if export succeeds, 503 if data is unavailable
        assert response.status_code in (200, 503)

        if response.status_code == 200:
            data = response.json()
            # Ensure "equipment" key exists in export payload
            assert "equipment" in data
            # Ensure "locations" key exists in export payload
            assert "locations" in data
