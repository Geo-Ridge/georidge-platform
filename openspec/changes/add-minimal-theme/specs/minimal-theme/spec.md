## ADDED Requirements

### Requirement: Map-only layout template
The system SHALL provide a `map-only` layout preset that renders a full-viewport map with no toolbar, no panels, no banner, and no status bar.

#### Scenario: Layout renders bare map
- **WHEN** a project's theme has `layout_preset` set to `"map-only"`
- **THEN** the viewer renders a full-viewport map with only a floating search bar and zoom controls visible

#### Scenario: No toolbar rendered
- **WHEN** the map-only layout is active
- **THEN** no toolbar, hamburger menu, or tool buttons are rendered in the DOM

#### Scenario: No panels rendered
- **WHEN** the map-only layout is active
- **THEN** no layers panel, feature info panel, legend panel, or slide-out panel is rendered in the DOM

#### Scenario: No banner rendered
- **WHEN** the map-only layout is active
- **THEN** no banner header is rendered regardless of the theme's `show_banner` setting

### Requirement: Floating search bar
The system SHALL render a search input floating over the map, positioned at the top center.

#### Scenario: Search input visible
- **WHEN** the map-only layout loads
- **THEN** a search input is visible, positioned at the top center of the viewport, overlaid on the map

#### Scenario: Search input triggers WFS search
- **WHEN** a user types 2 or more characters into the floating search input
- **THEN** the system sends a request to the existing `/viewer/<pk>/search/` endpoint and displays grouped results in a dropdown below the input

#### Scenario: Dropdown dismisses
- **WHEN** the user presses Escape or clicks outside the search area
- **THEN** the search results dropdown is hidden

### Requirement: Simple search result popup
The system SHALL display a lightweight popup when a user selects a search result from the dropdown.

#### Scenario: Popup appears on selection
- **WHEN** a user clicks a search result item in the dropdown
- **THEN** the map zooms to the feature extent and a small popup appears near the top of the map showing the result label, configured extra fields, and layer title

#### Scenario: Popup content
- **WHEN** the popup is displayed for a search result
- **THEN** the popup shows: (1) the label from the search result, (2) the values of `popup_fields` configured for that layer (if any), and (3) the layer title as a subtitle

#### Scenario: Popup dismisses
- **WHEN** the user clicks anywhere on the map outside the popup
- **THEN** the popup is hidden

#### Scenario: Popup repositions on new selection
- **WHEN** a user selects a different search result while the popup is visible
- **THEN** the popup updates its content to reflect the new result and remains visible

### Requirement: Search-select event dispatch
The search manager SHALL dispatch a `search-select` custom event when a user selects a result from the dropdown.

#### Scenario: Event dispatched with result data
- **WHEN** a user clicks a search result item
- **THEN** a `search-select` CustomEvent is dispatched on `document` with `detail` containing `{ label, layer_title, layer, bbox, geojson }`

### Requirement: Minimal JS payload
The map-only layout SHALL load only the JavaScript modules necessary for its functionality.

#### Scenario: Required scripts loaded
- **WHEN** the map-only layout renders
- **THEN** only `map-core.js`, `search-manager.js`, and `search-popup.js` are loaded (no `identify-manager.js`, `identify-popup.js`, `layer-manager.js`, `measure-tools.js`, `base-map-selector.js`, or `panel-resize.js`)
