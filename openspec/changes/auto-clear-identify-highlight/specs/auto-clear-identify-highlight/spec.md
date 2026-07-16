## ADDED Requirements

### Requirement: Closing or hiding an identify display clears the map highlight
The system SHALL automatically clear the on-map identify highlight when the user closes or fully hides/collapses any identify display (floating popup or dock/panel). The highlight MUST be removed without requiring a manual clear button. Switching tabs *within* a dock (e.g. Layers ⇄ Info) MUST NOT clear the highlight, because the identify display remains visible.

#### Scenario: Closing the floating identify popup clears the highlight
- **WHEN** a feature has been identified (popup + highlight visible) and the user closes the popup
- **THEN** the on-map highlight is removed

#### Scenario: Collapsing the info dock clears the highlight
- **WHEN** a feature has been identified (dock + highlight visible) and the user collapses/hides the dock/panel
- **THEN** the on-map highlight is removed

#### Scenario: Tab switch within a dock keeps the highlight
- **WHEN** the info dock is open and the user switches between tabs inside it (e.g. Layers ⇄ Info)
- **THEN** the on-map highlight remains

#### Scenario: Closing one of two simultaneous displays clears the highlight
- **WHEN** both a popup and a dock show the same identify result and the user closes/hides either one
- **THEN** the on-map highlight is removed

### Requirement: Manual clear-highlight button is removed
The system SHALL NOT provide a dedicated manual "Clear Highlight" / "Clear" button for identifying. Auto-clear on close/hide replaces it. The separate measure-clear control MUST remain unchanged.

#### Scenario: QWC2 layout has no clear-highlight button
- **WHEN** a user views the QWC2 layout toolbar
- **THEN** there is no "Clear Highlight" button (only Clear Measurements remains)

#### Scenario: MapStore layout has no clear-highlight button
- **WHEN** a user views the MapStore layout sidebar
- **THEN** there is no "Clear" identify button

#### Scenario: MapGuide layout has no clear-highlight button
- **WHEN** a user views the MapGuide layout info dock
- **THEN** the info-footer "Clear" button is absent

#### Scenario: Measure-clear remains available
- **WHEN** a user has drawn measurement geometry
- **THEN** the Clear Measurements control still removes measurement lines/polygons
