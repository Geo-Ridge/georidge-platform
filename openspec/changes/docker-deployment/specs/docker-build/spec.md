## ADDED Requirements

### Requirement: Multi-arch build pipeline
The system SHALL support building Docker images for multiple architectures using Docker Buildx.

#### Scenario: Build for current architecture
- **WHEN** user runs `docker compose build`
- **THEN** image is built for the current host architecture

#### Scenario: Build for multiple architectures
- **WHEN** user runs `docker buildx build --platform linux/amd64,linux/arm64`
- **THEN** images are built for both x86_64 and arm64 architectures

### Requirement: Build caching
The build pipeline SHALL use layer caching to speed up rebuilds.

#### Scenario: Rebuild after code change
- **WHEN** user modifies application code
- **THEN** only changed layers are rebuilt

#### Scenario: Dependency layer caching
- **WHEN** requirements.txt hasn't changed
- **THEN** dependency installation layer is cached

### Requirement: .dockerignore
The system SHALL provide a .dockerignore file to exclude unnecessary files from build context.

#### Scenario: Exclude dev artifacts
- **WHEN** Docker builds the image
- **THEN** .env, __pycache__, db.sqlite3, and media/ are excluded

#### Scenario: Small build context
- **WHEN** user runs docker build
- **THEN** build context size is minimized
