# Utility Infrastructure Knowledge Extraction API

A lightweight FastAPI application for equipment and maintenance data, extracting entities and exposing them via REST endpoints.

## Usage

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Linux/macOS
.venv\Scripts\activate       # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn main:app --reload
```
The application will start on `http://localhost:8000` with automatic API documentation at `/docs`.



## Testing
The project includes both pytest-based unit tests and command-line examples:
```bash
# Run all tests
pytest -v
```
Or use the manual command-line tests provided in:
***command-line-tests.md***




### Next Steps
Design decisions and assumptions will be added in the following commit.
