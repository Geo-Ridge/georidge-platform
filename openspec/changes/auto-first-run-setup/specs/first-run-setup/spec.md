## Purpose

Automates database initialization and default superuser creation so the application is immediately usable after the first container start with no manual intervention.

## ADDED Requirements

### Requirement: Auto-run migrations on first start

The system SHALL run Django database migrations automatically as part of container startup if the database does not contain the required tables.

#### Scenario: Fresh SQLite volume — migrations run

- **WHEN** the container starts with an empty or absent SQLite database file at `DJANGO_DB_NAME`
- **THEN** the system SHALL run `manage.py migrate --noinput` before binding the HTTP port

#### Scenario: Existing database — migrations skipped

- **WHEN** the container starts and the database already has all required tables
- **THEN** the system SHALL NOT re-run migrations

#### Scenario: PostGIS database — migrations run

- **WHEN** the container starts with `DJANGO_SETTINGS_MODULE=georidge_platform.settings.prod` and a PostGIS database configured via env vars
- **THEN** the system SHALL run migrations against the PostGIS database if tables are missing

### Requirement: Auto-create default superuser

The system SHALL create a default superuser account if no superuser exists after migrations complete.

#### Scenario: No superuser exists — superuser created

- **WHEN** no user with `is_superuser=True` exists after migrations
- **THEN** the system SHALL create a superuser with email from `DJANGO_SUPERUSER_EMAIL` (default `admin@georidge.local`) and password from `DJANGO_SUPERUSER_PASSWORD` (default `admin`)

#### Scenario: Superuser already exists — skipped

- **WHEN** a superuser already exists after migrations
- **THEN** the system SHALL NOT modify existing users or create additional superusers

### Requirement: Default superuser configurable via environment variables

The system SHALL allow the default superuser email and password to be overridden through environment variables.

#### Scenario: Custom email and password

- **WHEN** `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` are set
- **THEN** the created superuser SHALL use those values instead of defaults

#### Scenario: Only email set

- **WHEN** only `DJANGO_SUPERUSER_EMAIL` is set
- **THEN** the superuser SHALL use the specified email and the default password

### Requirement: Gunicorn starts only after setup completes

The system SHALL only start the Gunicorn WSGI server after migrations and superuser creation have completed successfully.

#### Scenario: Migration failure — gunicorn does not start

- **WHEN** database migrations fail
- **THEN** the system SHALL log the error and exit with a non-zero status code
- **AND** the Gunicorn server SHALL NOT start
