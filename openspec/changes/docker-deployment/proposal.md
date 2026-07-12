## Why

The project currently runs only on Windows via Waitress with OSGeo4W Python. There's no portable, reproducible way to deploy it. Docker enables running on any platform (Linux, Mac, Windows, cloud), simplifies onboarding, and supports multi-arch builds (x86 + arm64).

## What Changes

- Add `Dockerfile` — multi-stage build for the Django app (Python 3.12, Gunicorn, build deps for psycopg2/Pillow)
- Add `docker-compose.yml` — orchestrates Django app + QGIS Server containers
- Add `.dockerignore` — excludes dev artifacts from build context
- Switch WSGI server from Waitress (Windows-only) to Gunicorn (Linux/Docker)
- QGIS Server runs as a separate container, connected via internal Docker network

## Capabilities

### New Capabilities
- `docker-app`: Dockerfile for the Django application with multi-arch support (x86, arm64)
- `docker-compose`: Compose file orchestrating Django app + QGIS Server + volumes
- `docker-build`: Multi-arch build pipeline using Docker Buildx

### Modified Capabilities

## Impact

- New files: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- Modified: `requirements.txt` (already updated with gunicorn, psycopg2)
- Runtime: Gunicorn replaces Waitress in Docker (Waitress .bat still works for local Windows dev)
- QGIS Server: now a container (`qgis/qgis-server` image) instead of local OSGeo4W install
