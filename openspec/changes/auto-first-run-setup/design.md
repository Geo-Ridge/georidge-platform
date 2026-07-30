## Context

The application starts Gunicorn which imports `georidge_platform.wsgi`, which calls `django.setup()`. Currently `wsgi.py` calls a no-op `configure_pyqgis()` and sets the default settings module to `prod` (requiring PostGIS). The Dockerfile runs migrations at build time, but the SQLite path (`/app/data/db.sqlite3`) is inside a volume mount — the build-time DB is discarded.

The startup sequence needs to intercept before Gunicorn binds the port, run migrations and superuser creation if needed, then start serving.

## Goals / Non-Goals

**Goals:**
- Single startup module that runs before Gunicorn
- Detect fresh volume vs. existing database
- Run migrations only when tables are missing
- Create superuser only when none exists
- Configurable defaults through env vars
- Works with both SQLite (`dev`) and PostGIS (`prod`) settings
- Remove dead code (`configure_pyqgis`) that does nothing on Linux

**Non-Goals:**
- Not modifying the existing Docker Compose setup
- Not changing the existing app logic or models
- Not adding a management command or CLI entrypoint
- Not adding a health check endpoint for setup status

## Decisions

### Decision: Startup as a wsgi.py import hook vs. separate entrypoint script

**Chosen:** Import hook in `wsgi.py`

The alternative was a separate shell script (like `georidge-startup.sh`) mounted as a volume and overriding `CMD`. That works for our Podman deployment but isn't baked into the image — users who `docker run` the image without the mount won't get auto-setup.

By putting the logic in `wsgi.py`, it runs every time the WSGI application loads — whether started by Gunicorn, uWSGI, or `manage.py runserver`. This makes it part of the image, not the deployment.

**Trade-off:** The startup logic runs in the same process as Gunicorn. If migration fails, the process exits and Gunicorn dies — which is exactly the desired behavior (see spec: gunicorn doesn't start on migration failure).

### Decision: Detect fresh volume by attempting a DB query vs. checking file existence

**Chosen:** Try a query, catch exception

Checking if a SQLite file exists doesn't work for PostGIS. Running `migrate` unconditionally on every start is slow and noisy. Instead, try a simple query (`User.objects.exists()`) and run migrations only if it raises `OperationalError`.

This works for both SQLite and PostGIS: if tables are missing, the query fails, migrations run, query succeeds on retry.

**Alternatives considered:**
- Check `Connection.introspection.table_names()` — more direct but requires `django.setup()` first
- Check file existence for SQLite — doesn't work for PostGIS
- Run `migrate --check` — Django 5.x feature, but django-cms and some apps don't support it

### Decision: Conditional import in wsgi.py vs. unconditional import

**Chosen:** Unconditional import of `startup.run_startup()`

The module is small and has no heavy dependencies — it imports Django ORM which is already loaded. An unconditional import is simpler and the function returns quickly when no action is needed (single `User.objects.exists()` query).

### Decision: Default settings module changed to `dev`

The current default in `wsgi.py` is `prod` which crashes without PostGIS env vars. Changing it to `dev` means a plain `docker run` works out of the box, and users who want PostGIS override with `DJANGO_SETTINGS_MODULE`.

### Decision: Remove `configure_pyqgis()` calls

The function iterates a list of Windows-only paths and returns `False` on Linux. It's called at import time in both `wsgi.py` and `manage.py`. Removing these calls:
- Eliminates a misleading import (looks important, does nothing)
- Avoids the confusing `candidates` list with Windows paths in Linux containers
- The QGIS Server connection is handled via HTTP to the `qgis-server` container, not via embedded PyQGIS

## Risks / Trade-offs

- **Migration failure during startup** → Container exits, orchestration restarts it. On a persistent issue (e.g., PostGIS unreachable), this creates a restart loop. Mitigation: error logging includes the full traceback, and the exit code is non-zero so orchestrators can apply backoff.
- **Startup time increased** → The first start is slower because migrations run. Subsequent starts add ~50ms for the `User.objects.exists()` check. Acceptable — migrations are a one-time cost.
- **`wsgi.py` imports startup module** → If `startup.py` has an import error, the entire app fails to start. Mitigation: `startup.py` has minimal imports (Django ORM, `call_command`).
