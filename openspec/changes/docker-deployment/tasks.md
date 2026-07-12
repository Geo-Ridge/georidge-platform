## 1. Docker Configuration Files

- [x] 1.1 Create `.dockerignore` file excluding `.env`, `__pycache__`, `db.sqlite3`, `media/`, `.git`, `node_modules`
- [x] 1.2 Create `Dockerfile` with Python 3.12 base image, build dependencies (gcc, libpq-dev, python3-dev), and Gunicorn
- [x] 1.3 Create `docker-compose.yml` with Django app and QGIS Server services

## 2. Dockerfile Implementation

- [x] 2.1 Set working directory and copy requirements.txt
- [x] 2.2 Install system dependencies for psycopg2 and Pillow compilation
- [x] 2.3 Install Python dependencies from requirements.txt
- [x] 2.4 Copy application code to container
- [x] 2.5 Run Django migrations and collect static files
- [x] 2.6 Configure Gunicorn as entrypoint with health check endpoint

## 3. Docker Compose Implementation

- [x] 3.1 Define Django app service with environment variables
- [x] 3.2 Define QGIS Server service using `qgis/qgis-server` image
- [x] 3.3 Create internal network for app ↔ QGIS communication
- [x] 3.4 Define named volumes for media files and SQLite database
- [x] 3.5 Configure service dependencies and health checks

## 4. Environment Configuration

- [x] 4.1 Update `.env.example` with Docker-specific variables (QGIS_SERVER_URL, ALLOWED_HOSTS)
- [x] 4.2 Ensure `dev.py` settings work with Docker (SQLite path, QGIS_SERVER_URL)

## 5. Testing and Validation

- [ ] 5.1 Test Docker build on x86_64 architecture
- [ ] 5.2 Test Docker build on arm64 architecture (if available)
- [ ] 5.3 Test `docker compose up` starts both services
- [ ] 5.4 Verify QGIS Server is accessible from Django app
- [ ] 5.5 Verify static files are served correctly
- [ ] 5.6 Verify media uploads persist across container restarts
