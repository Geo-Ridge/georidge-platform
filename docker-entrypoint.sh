#!/bin/sh
set -e

if [ "$(id -u)" = "0" ]; then
    # Ensure runtime directories are writable by the app user
    # (named volumes start out root-owned on first use)
    mkdir -p /app/data /app/media
    chown -R app:app /app/data /app/media

    # (Re)collect static files using the active settings module. The build-time
    # collectstatic runs under the default (dev) settings; running it again here
    # with the final settings generates the Whitenoise manifest that prod needs.
    python manage.py collectstatic --noinput

    # Drop privileges and run the CMD (gunicorn) as the app user
    exec setpriv --reuid=app --regid=app --init-groups "$@"
fi

# Already running as a non-root user (e.g. `docker run --user app`): run directly
exec "$@"
