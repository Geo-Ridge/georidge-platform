## Context

The GeoRidge Platform currently runs on Windows via Waitress with OSGeo4W Python. This limits deployment to Windows-only environments and makes onboarding difficult. Docker enables cross-platform deployment, reproducible environments, and cloud readiness.

Key components:
- Django application (Python 3.12, Gunicorn)
- QGIS Server (for map rendering)
- SQLite database (dev mode) / PostGIS (prod mode)
- Static files served via Whitenoise

## Goals / Non-Goals

**Goals:**
- Single `docker compose up` command to run the entire platform
- Multi-arch support: x86_64 and arm64 (Apple Silicon)
- Reproducible builds with pinned dependencies
- QGIS Server as a containerized service

**Non-Goals:**
- Production-grade Kubernetes deployment
- SSL/TLS termination (handled by reverse proxy in production)
- Database migration from SQLite to PostGIS

## Decisions

1. **Single-stage build vs Multi-stage build**
   - Decision: Single-stage build
   - Rationale: Simpler Dockerfile, faster builds for development. Multi-stage can be added later for production optimization.
   - Alternative: Multi-stage build (slower dev iteration, smaller image)

2. **QGIS Server: Embedded vs Separate container**
   - Decision: Separate container (`qgis/qgis-server` official image)
   - Rationale: Official image is maintained, isolates QGIS from app, easier upgrades
   - Alternative: Embed QGIS in app container (complex, harder to maintain)

3. **SQLite vs PostGIS in Docker**
   - Decision: SQLite for dev mode in Docker
   - Rationale: Zero configuration, matches local dev experience. PostGIS available via `prod.py` settings.
   - Alternative: PostGIS in Docker (more realistic, but adds complexity)

4. **Network configuration**
   - Decision: Internal Docker network for app ↔ QGIS communication
   - Rationale: Secure, no external exposure of QGIS Server
   - Alternative: Expose QGIS on host (security risk)

5. **Volume mounts**
   - Decision: Named volumes for media, SQLite DB
   - Rationale: Persistent data across container restarts
   - Alternative: Bind mounts (less portable)

## Risks / Trade-offs

1. **Multi-arch build complexity** → Mitigated by using `docker buildx` with QEMU
2. **SQLite limitations** → Acceptable for dev; production uses PostGIS
3. **QGIS Server image size** → ~1GB, but unavoidable for full QGIS functionality
4. **No SSL in Docker** → Mitigated by adding reverse proxy (Traefik/Nginx) in production compose
