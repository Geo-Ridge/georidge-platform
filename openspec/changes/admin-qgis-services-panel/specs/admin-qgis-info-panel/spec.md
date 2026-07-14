## ADDED Requirements

### Requirement: QGIS Server paths display
The admin change form SHALL display the project's local file path and QGIS Server remapped path as read-only text.

#### Scenario: Paths shown for existing project
- **WHEN** admin opens the change form for an existing project with a file uploaded
- **THEN** the form displays the local path (e.g., `/app/media/projects/1/.../file.qgz`) and the remapped QGIS Server path (e.g., `/var/www/qgis-server/media/projects/1/.../file.qgz`)

#### Scenario: No file uploaded
- **WHEN** admin opens the change form for a project with no file
- **THEN** the paths section shows "No file uploaded"

### Requirement: WMS service status
The admin change form SHALL show WMS service availability with layer count and queryable layer count.

#### Scenario: WMS online with layers
- **WHEN** admin opens the change form and QGIS Server WMS responds successfully
- **THEN** the form shows a green "Online" indicator, the total layer count, and the number of queryable layers

#### Scenario: WMS offline
- **WHEN** admin opens the change form and QGIS Server WMS is unreachable or returns an error
- **THEN** the form shows a red "Offline" indicator with a brief error message

### Requirement: WFS service status
The admin change form SHALL show WFS service availability.

#### Scenario: WFS online
- **WHEN** admin opens the change form and QGIS Server WFS responds successfully
- **THEN** the form shows a green "Online" indicator

#### Scenario: WFS offline
- **WHEN** admin opens the change form and QGIS Server WFS is unreachable
- **THEN** the form shows a red "Offline" indicator

### Requirement: Capabilities XML links
The admin change form SHALL provide links to raw WMS and WFS GetCapabilities XML documents.

#### Scenario: WMS capabilities link
- **WHEN** admin views the QGIS Server section
- **THEN** a link labeled "WMS Capabilities" points to the WMS GetCapabilities URL and opens in a new tab

#### Scenario: WFS capabilities link
- **WHEN** admin views the QGIS Server section
- **THEN** a link labeled "WFS Capabilities" points to the WFS GetCapabilities URL and opens in a new tab

### Requirement: Section is collapsible
The QGIS Server section SHALL be collapsible and collapsed by default.

#### Scenario: Section collapsed by default
- **WHEN** admin opens the change form
- **THEN** the QGIS Server section is collapsed and can be expanded

#### Scenario: Section remembers state
- **WHEN** admin expands or collapses the QGIS Server section
- **THEN** the section stays in that state for the duration of the page session
