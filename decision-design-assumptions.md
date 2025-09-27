# Decision Design & Assumptions
This document outlines the main design decisions and assumptions made during the implementation of the **Utility Infrastructure Knowledge API** coding challenge.  

- **Context**: Each section is structured around a decision, the underlying assumptions, and how it fits within the challenge constraints.  
- **Optimization**: Where relevant, potential improvements for a real-world production system are discussed. These focus on practical, in-the-box methods and avoid NLP pipelines or other heavy frameworks outside the project scope.  



## 1. Architecture
**Decision**  
- A lightweight **FastAPI** application was chosen to build the REST API.  
- FastAPI is modern, async-ready, and includes automatic documentation (Swagger UI and ReDoc).  
- It requires minimal dependencies and fits well with the challenge requirements.  

**Assumption**  
- No external database is used.  
- Data is loaded from CSV and JSON files and kept in-memory for queries.  

**Real-world optimization:**  
- In an in-the-box scenario (without NLP pipelines), introducing a database like **PostgreSQL** would improve persistence, scalability, and durability of equipment and maintenance data.  



## 2. Data Processing
**Decision:**  
- Data ingestion is handled with *pandas* for CSVs and the *json* library for JSON logs.  
- A `DataStore` class was introduced to hold equipment and maintenance DataFrames.

**Assumption:**  
- CSV files must include at least: `equipment_id`, `equipment_type`, `location`.  
- JSON logs must include: `log_id`, `equipment_id`, `maintenance_type`, `date`, `description`.  
- These assumptions ensure that a minimal schema is always present so entity extraction and relationships (e.g., joining on `equipment_id`) work reliably.

**Real-world optimization:**  
- Schema validation could be extended using *Pydantic* models, with separate schemas for larger or more complex datasets.
- This would enforce stricter typing, validate ranges (e.g., for dates, costs, IDs), and ensure proper formatting (e.g., date parsing, non-empty strings).
- Such validation would reduce the risk of invalid or inconsistent input data in production.  



## 3. Entity Extraction
**Decision**  
- Entities are extracted from the provided files:  
  - Equipment → from CSV.  
  - Maintenance logs → from JSON.  
  - Locations → derived from equipment data.  
- Extraction is kept schema-light to stay simple and transparent.

**Assumption**  
- Optional fields like `manufacturer`, `model`, `technician`, and `status` may or may not be present.  
- `equipment_id` is used to link equipment and maintenance records; uniqueness is assumed but not enforced in this prototype.  

**Real-world optimization:**  
- Entities could be normalized into related tables or cached mappings (e.g., `equipment → maintenance`, `location → equipment`).
- Uniqueness of keys like `equipment_id` and `log_id` should be validated through schema checks or database constraints.
- For more advanced use cases, relationships could also be represented in a lightweight knowledge graph (e.g., equipment nodes connected to maintenance and location nodes).  



## 4. API Design
**Decision**  
REST endpoints were implemented under `/api`:  
- `GET /equipment` → list equipment.  
- `GET /locations` → list locations.  
- `GET /maintenance` → list maintenance logs.  
- `GET /search?query=` → substring search across entities.  
- `POST /process` → upload new CSV/JSON files.  
- `GET /export` → export nested JSON view.  

All endpoints are grouped under a single **API** tag in the documentation to keep the interface simple.  

**Assumption**  
- Keyword search is substring-based and case-insensitive.  
- The dataset size is small enough that all records can be returned in a single response without pagination.  

**Real-world optimization:**  
- In a production setting, the API could be extended with pagination, sorting, and field-based filtering to handle larger datasets efficiently.
- Upload endpoints would benefit from stricter schema validation and consistent error responses.
- To improve performance, frequently accessed resources (like /equipment or /locations) could also be cached, and lightweight mechanisms such as ETags could minimize unnecessary payload transfers.
- For larger projects, documentation tags could be split by domain (e.g., **Equipment**, **Maintenance**, **Data**) to improve navigation, while here simplicity and clarity take priority.  



## 5. Error Handling
**Decision**  
- A dedicated `DataUnavailableError` exception class was implemented to standardize **HTTP 503** responses when required data is missing, avoiding repeated code in each API endpoint.  
- **HTTP 422** is raised for invalid file uploads.  
- **HTTP 404** is returned for search queries with no matches.  

**Assumption**  
- Clients are expected to handle both normal errors and edge cases gracefully.  
- Examples of edge cases include: missing files, empty datasets, invalid schemas, or searches yielding no results.  
 
**Real-world optimization**  
- Documenting **503 errors** in auto-generated docs (Swagger, ReDoc) is not always smooth with the current setup, since custom exceptions do not automatically appear in OpenAPI schema.  
- Extend error payloads to include structured fields (`error`, `hint`, `code`) for easier client-side parsing.  
- Integrate with monitoring/alerting systems (e.g., Prometheus, ELK stack) to detect recurring issues.  



## 6. Logging
**Decision**  
- Logging is configured centrally in `logger.py` to keep it consistent across modules.  
- Both console and daily file logging are supported (`logs/app_YYYY-MM-DD.log`).
- Logging was added even though FastAPI provides automatic API docs, because runtime behavior, errors, and unexpected data conditions need persistent records beyond request/response documentation.  

**Assumption**  
- No `.env` file is required in this setup; logging works out of the box.  
- Logs are always written to a `logs/` directory in the project root. A new file is created per day (app_YYYY-MM-DD.log) and grows without rotation, since runs are short-lived.
- Log level is fixed to `INFO` for both console and file outputs, meaning debug details are not captured.  

**Real-world optimization**  
- Extend logging with additional levels (`DEBUG`, `WARNING`, `ERROR`, `CRITICAL`) depending on environment (development vs. production).  
- Use `.env` configuration to control log level, log file rotation, or external logging backends (e.g., `LOG_LEVEL=DEBUG`, `LOG_DIR=/var/log/app`).
- log rotation (e.g., via TimedRotatingFileHandler or system tools like logrotate) should be added to prevent individual log files from growing indefinitely.
- Switch to structured logging (e.g., JSON format) and forward logs to centralized systems such as ***ELK*** or ***Grafana Loki*** for better observability and analytics.  



## 7. Testing  
**Decision**  
- Unit tests were implemented using **pytest** to validate data processing (CSV/JSON loading, entity extraction) and API endpoints.  
- We use FastAPI’s **TestClient** with pytest for automated testing, which aligns with my stronger familiarity with Python-based testing, runs the app fully in-memory without a server, making tests fast, reliable, reproducible and CI-friendly. 

**Assumption**  
- Tests cover both success and error scenarios (e.g., valid vs. invalid files, data available vs. unavailable).  
- Schema checks in tests assume the minimal required fields are always present in sample data.  
- The only additional library introduced for project is **httpx**, which is required internally by FastAPI’s `TestClient`. This kept the testing setup minimal while ensuring full compatibility with FastAPI.  

**Real-world optimization**  
- Extend coverage with edge cases (very large files, malformed records, concurrent uploads).  
- Add integration tests with preloaded datasets to guarantee deterministic 200 responses in addition to error scenarios.  
- Include performance tests and CI/CD integration to automatically validate changes.  



## Final Note
- For this submission, a simple Python venv was used to keep setup minimal and transparent, ensuring dependencies are installed exactly as listed in requirements.txt without extra tooling.  
- In a real development workflow, I would use **make** to streamline common tasks like setup, running, and testing, and rely on **Docker Compose** to run the application seamlessly as a microservice and guarantee consistent environments.  
- Beyond the current scope, a production-ready system could also benefit from **type annotation tools**, **linting**, and **automated testing in a CI/CD pipeline** to ensure stability with every change.  
- Security features such as authentication (e.g., JWT) and rate limiting would be required in a real project to protect endpoints.  
- Performance scaling could be achieved with asynchronous database access and caching layers for frequently queried data.  
- Over time, more advanced methods could be introduced, including **knowledge graphs** to capture and query relationships more richly, or applying **AI/NLP techniques** to process unstructured maintenance reports.  
- With the power of **LLMs and AI agents**, such a system could even learn to integrate unstructured data automatically, extending this lightweight prototype into a robust knowledge platform for utility infrastructure.  
