
```bash
# List all equipment
curl -s -X GET "http://localhost:8000/api/equipment" -H "accept: application/json" | python -m json.tool

# List all locations
curl -s -X GET "http://localhost:8000/api/locations" -H "accept: application/json" | python -m json.tool

# List all maintenance logs
curl -s -X GET "http://localhost:8000/api/maintenance" -H "accept: application/json" | python -m json.tool

# Search for equipment/maintenance by keyword
curl -s -X GET "http://localhost:8000/api/search?query=Switch" -H "accept: application/json" | python -m json.tool

# Upload new CSV + JSON files (replace with your local paths)
curl -s -X POST "http://localhost:8000/api/process" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "equipment_file=@data/equipment_inventory.csv" \
  -F "maintenance_file=@data/maintenance_logs.json" | python -m json.tool

# Export combined equipment + maintenance logs
curl -s -X GET "http://localhost:8000/api/export" -H "accept: application/json" | python -m json.tool
```