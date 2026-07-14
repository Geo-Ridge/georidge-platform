## ADDED Requirements

### Requirement: Parse tab structure from QGS XML regardless of attribute order
The system SHALL parse `<attributeEditorContainer>` elements with `type="Tab"` from the QGS XML to extract tab names and their field lists, regardless of the order in which `name` and `type` attributes appear in the XML.

#### Scenario: Tab container with name before type
- **WHEN** the QGS XML contains `<attributeEditorContainer name="General" type="Tab">` with nested `<attributeEditorField name="FIELD_A">`
- **THEN** the parser SHALL return `[{"name": "General", "fields": ["FIELD_A"]}]`

#### Scenario: Tab container with type before name
- **WHEN** the QGS XML contains `<attributeEditorContainer type="Tab" name="Main">` with nested `<attributeEditorField name="FIELD_B">`
- **THEN** the parser SHALL return `[{"name": "Main", "fields": ["FIELD_B"]}]`

#### Scenario: No attributeEditorForm in project
- **WHEN** the QGS XML has no `<attributeEditorForm>` section
- **THEN** the parser SHALL return an empty list `[]`

#### Scenario: Multiple tabs with mixed attribute ordering
- **WHEN** the QGS XML contains multiple `<attributeEditorContainer type="Tab">` elements with different attribute orderings
- **THEN** the parser SHALL return all tabs with their correct names and field lists

### Requirement: Detect image fields from QGS XML regardless of attribute order
The system SHALL detect fields using `ExternalResource` image widgets by checking for `editWidget type="ExternalResource"` containing a `DocumentViewer` option with value `1`, regardless of the order of attributes within the `<Option>` element.

#### Scenario: DocumentViewer with name before value
- **WHEN** the QGS XML contains `<Option name="DocumentViewer" type="int" value="1"/>` inside an `<editWidget type="ExternalResource">`
- **THEN** the field SHALL be detected as an image field

#### Scenario: DocumentViewer with value before name
- **WHEN** the QGS XML contains `<Option value="1" type="int" name="DocumentViewer"/>` inside an `<editWidget type="ExternalResource">`
- **THEN** the field SHALL be detected as an image field

#### Scenario: ExternalResource without DocumentViewer
- **WHEN** the QGS XML contains `<editWidget type="ExternalResource">` but no `DocumentViewer` option with value `1`
- **THEN** the field SHALL NOT be detected as an image field

### Requirement: Always produce feature tabs from properties
The system SHALL always produce a non-empty `feature_tabs` result when features are present, even if the QGS XML tab structure parsing returns empty. When no tab structure is found, all feature properties SHALL be grouped into a single "Attributes" tab.

#### Scenario: Features present with tab structure
- **WHEN** features are returned from WMS and tab structure is parsed from QGS XML
- **THEN** feature properties SHALL be grouped by tab with media items for image fields

#### Scenario: Features present without tab structure
- **WHEN** features are returned from WMS but tab structure parsing returns empty
- **THEN** all feature properties SHALL be grouped into a single tab named "Attributes"

#### Scenario: No features returned
- **WHEN** WMS returns no features
- **THEN** feature tabs SHALL be empty
