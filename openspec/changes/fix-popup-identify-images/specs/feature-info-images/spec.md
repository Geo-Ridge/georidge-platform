## ADDED Requirements

### Requirement: Popup receives structured feature data
The `identify-complete` event SHALL include pre-parsed `featureTabs` and `qgisHtml` in its detail, so the popup does not need to re-parse JSON from HTML.

#### Scenario: Event includes featureTabs
- **WHEN** `identify-manager.js` dispatches `identify-complete` with parsed `featureTabs` data
- **THEN** `event.detail.featureTabs` contains the parsed array of tab objects (each with `name`, `fields`, `media`)

#### Scenario: Event includes qgisHtml
- **WHEN** `identify-manager.js` dispatches `identify-complete` with parsed `qgisHtml` data
- **THEN** `event.detail.qgisHtml` contains the parsed HTML string

### Requirement: Popup renders images from structured data
The identify popup SHALL display images from ExternalResource fields when `featureTabs` data is provided in the event detail.

#### Scenario: featureTabs with media present
- **WHEN** the popup receives `event.detail.featureTabs` containing tabs with `media` entries
- **THEN** the popup renders `<img>` elements for each media entry with a valid image URL

#### Scenario: featureTabs empty, qgisHtml present
- **WHEN** `event.detail.featureTabs` is null/empty and `event.detail.qgisHtml` is present
- **THEN** the popup renders the QGIS HTML content with media elements

#### Scenario: No structured data, fallback to data-tabs
- **WHEN** `event.detail.featureTabs` is null/empty and `event.detail.qgisHtml` is null
- **THEN** the popup falls back to parsing `data-tabs` from the HTML (which is not stripped by the manager)
