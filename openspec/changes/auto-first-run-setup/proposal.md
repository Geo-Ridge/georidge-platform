## Why

The georidge-platform Docker image requires manual steps after first run — database migrations must be executed and a superuser created before anyone can log in. A user who builds and runs the image without reading the docs hits 500 errors and missing tables. This change makes the image truly ready-to-go: build, run, log in.

## What Changes

- Add a `startup.py` module that auto-runs migrations and creates a default superuser on first container start
- Set `wsgi.py` default settings module to `dev` (SQLite) instead of `prod` (PostGIS) — the current default crashes without PostGIS env vars
- Remove the no-op `call to configure_pyqgis()` from `wsgi.py` and `manage.py` — it only checks a Windows path and does nothing on Linux
- Remove the build-time `RUN python manage.py migrate` from `Dockerfile` — migrations are now handled at runtime, and the build-time migrate is discarded by volume mounts anyway
- Update example env files with new `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` vars

## Capabilities

### New Capabilities
- `first-run-setup`: automatic database initialization and default superuser creation on first container start

### Modified Capabilities

<!-- No existing capabilities are changing — this is purely a startup/initialization concern -->

## Impact

- `georidge_platform/startup.py` — new module
- `georidge_platform/wsgi.py` — import and call startup, change default settings module, remove qgis_setup call
- `manage.py` — remove qgis_setup call
- `Dockerfile` — remove `RUN python manage.py migrate --noinput`
- `.env.linux.example`, `.env.win.example` — add superuser env vars
