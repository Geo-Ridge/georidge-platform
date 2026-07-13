## ADDED Requirements

### Requirement: popup_fields admin field
The `LayerSearchConfig` model SHALL include a `popup_fields` field that accepts a comma-separated list of WFS property names to display in the search result popup.

#### Scenario: Field exists on model
- **WHEN** a `LayerSearchConfig` instance is created or edited
- **THEN** the `popup_fields` field accepts a comma-separated string of field names (e.g., `"section, lot, block"`)

#### Scenario: Field empty by default
- **WHEN** a new `LayerSearchConfig` is created without specifying `popup_fields`
- **THEN** `popup_fields` defaults to an empty string

#### Scenario: Field visible in admin
- **WHEN** an admin views the `LayerSearchConfig` edit form
- **THEN** the `popup_fields` field is visible and editable as a text input

### Requirement: popup_fields exposed in map-config JSON
The system SHALL include `popup_fields` for each active search config in the map-config JSON embedded in the viewer page.

#### Scenario: Config includes popup_fields per layer
- **WHEN** the map-only layout renders its `<script id="map-config">` block
- **THEN** the JSON includes a `searchConfigs` array where each entry has `{ layer, popup_fields }` with `popup_fields` parsed from the comma-separated string to an array of trimmed strings

#### Scenario: Empty popup_fields parsed correctly
- **WHEN** a search config has `popup_fields` set to `""` (empty string)
- **THEN** the corresponding `popup_fields` in map-config JSON is an empty array `[]`

### Requirement: Frontend popup uses popup_fields
The search popup component SHALL display only the fields listed in `popup_fields` for the matching layer.

#### Scenario: Fields filtered by config
- **WHEN** a search result is selected and its layer has `popup_fields: ["section", "lot"]`
- **THEN** the popup shows the label, then "Section: B" and "Lot: 12" (from the feature's properties), then the layer title

#### Scenario: Missing field silently skipped
- **WHEN** a `popup_fields` entry references a property that does not exist in the feature's GeoJSON properties
- **THEN** that field is silently omitted from the popup (no error, no placeholder)

#### Scenario: No popup_fields configured
- **WHEN** a search result is selected and its layer has no `popup_fields` config or an empty array
- **THEN** the popup shows only the label and layer title (no extra fields)
