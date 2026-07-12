## ADDED Requirements

### Requirement: Docker Compose orchestration
The system SHALL provide a docker-compose.yml file that orchestrates Django app and QGIS Server containers.

#### Scenario: Start all services
- **WHEN** user runs `docker compose up`
- **THEN** both Django app and QGIS Server containers start successfully

#### Scenario: Service dependency
- **WHEN** Django app starts
- **THEN** it waits for QGIS Server to be ready

### Requirement: QGIS Server container
The compose file SHALL include QGIS Server as a separate container using the official `qgis/qgis-server` image.

#### Scenario: QGIS Server accessible
- **WHEN** containers are running
- **THEN** QGIS Server is accessible on internal network port 80

#### Scenario: QGIS Server configuration
- **WHEN** QGIS Server starts
- **THEN** it uses environment variables for configuration

### Requirement: Volume mounts
The compose file SHALL define named volumes for persistent data.

#### Scenario: Media files persist
- **WHEN** user uploads files
- **THEN** files persist across container restarts

#### Scenario: SQLite database persists
- **WHEN** application writes to database
- **THEN** database file persists across container restarts

### Requirement: Network configuration
The compose file SHALL create an internal network for container communication.

#### Scenario: App to QGIS communication
- **WHEN** Django app needs to render maps
- **THEN** it communicates with QGIS Server via internal network

#### Scenario: No external QGIS exposure
- **WHEN** containers are running
- **THEN** QGIS Server is not exposed to host machine
