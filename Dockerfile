FROM python:3.12.13-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DB_NAME=/app/data/db.sqlite3

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2, Pillow, and GDAL (PostGIS prod support).
# Privilege drop to the non-root user is done with setpriv (from util-linux, always present).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user to run the application, with a writable home
# (gunicorn's control socket defaults to $HOME/.gunicorn)
RUN useradd --system --no-create-home --uid 10001 app \
    && mkdir -p /home/app \
    && chown app:app /home/app
ENV HOME=/home/app

# Copy application code
COPY . .

# Ensure data directory exists for SQLite
RUN mkdir -p /app/data && chown -R app:app /app/data

# Collect static files (dev settings default; regenerated at startup with the active settings)
RUN python manage.py collectstatic --noinput

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Healthcheck: /admin/login/ returns 200 when the app is up. It is exempt from
# the tenancy middleware (which would 404 tenant-less paths like /qgis-server/status/).
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/admin/login/', timeout=5)"

# Entrypoint drops privileges to the non-root app user before running the CMD
ENTRYPOINT ["docker-entrypoint.sh"]

# Configure Gunicorn as entrypoint
CMD ["gunicorn", "georidge_platform.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--preload"]
