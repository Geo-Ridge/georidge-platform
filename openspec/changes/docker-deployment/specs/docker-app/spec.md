## ADDED Requirements

### Requirement: Dockerfile for Django application
The system SHALL provide a Dockerfile that builds the Django application with Python 3.12, Gunicorn, and all necessary dependencies.

#### Scenario: Build Docker image
- **WHEN** user runs `docker build -t georidge-platform .`
- **THEN** image is built successfully with all dependencies installed

#### Scenario: Multi-arch support
- **WHEN** user builds for x86_64 or arm64 architecture
- **THEN** image runs correctly on both architectures

### Requirement: Build dependencies
The Dockerfile SHALL include build dependencies for psycopg2 and Pillow compilation.

#### Scenario: psycopg2 compilation
- **WHEN** Docker image is built
- **THEN** psycopg2-binary is installed successfully

#### Scenario: Pillow compilation
- **WHEN** Docker image is built
- **THEN** Pillow is installed with JPEG/PNG support

### Requirement: Gunicorn WSGI server
The Docker container SHALL use Gunicorn as the WSGI server instead of Waitress.

#### Scenario: Gunicorn starts
- **WHEN** container starts
- **THEN** Gunicorn serves the Django application on port 8000

#### Scenario: Health check
- **WHEN** container is running
- **THEN** health endpoint responds with 200 OK

### Requirement: Static file serving
The container SHALL serve static files via Whitenoise middleware.

#### Scenario: Static files accessible
- **WHEN** user requests `/static/` path
- **THEN** static files are served correctly
