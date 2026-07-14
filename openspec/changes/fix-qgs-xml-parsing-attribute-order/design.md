## Context

The viewer's identify endpoint (`views.py:identify_view`) parses the QGIS project file (.qgz) to extract:
1. **Tab structure**: Which fields belong to which tabs (from `<attributeEditorContainer type="Tab">` elements)
2. **Image fields**: Which fields use ExternalResource image widgets (from `<editWidget type="ExternalResource">` with `DocumentViewer` config)

Both parsers currently use regex/substring matching that assumes a specific XML attribute ordering. QGIS 3.40+ serializes attributes alphabetically, breaking both parsers silently.

The working project (Chenango_County, created in older QGIS) has `name` before `type` in attribute containers. The broken project (img, created in QGIS 3.40.5) has `type` before `name`.

## Goals / Non-Goals

**Goals:**
- Parse tab structure and image fields regardless of XML attribute ordering
- Maintain backward compatibility with existing QGIS projects
- Add graceful fallback when tab structure parsing yields no results
- Keep the implementation simple — use Python's built-in `xml.etree.ElementTree` which is already imported in `services.py`

**Non-Goals:**
- Changing the frontend rendering logic (already works correctly)
- Changing the QGIS Server WMS query logic
- Supporting QGIS project formats beyond what QGIS 3.x produces
- Refactoring the entire identify pipeline

## Decisions

### Decision 1: Use `xml.etree.ElementTree` for XML parsing

**Choice**: Parse the .qgs XML with `xml.etree.ElementTree` instead of regex.

**Rationale**: The QGS file is valid XML. `xml.etree.ElementTree` is already imported in `services.py` and handles attribute access via `element.attrib.get()` which is order-agnostic. Regex on XML is inherently fragile — attribute ordering, whitespace, and quoting variations all cause failures.

**Alternative considered**: Make the regex attribute-order-agnostic with `(?:[^>]*?name="([^"]*)")?[^>]*?(?:type="Tab")?` — rejected because it becomes unreadable and still fragile to other XML variations.

### Decision 2: Parse the .qgs XML once, extract both tab structure and image fields

**Choice**: Read the .qgs content once via `_read_qgs_from_qgz()`, then pass the parsed XML tree to both `parse_qgs_tab_structure()` and `parse_qgs_external_resource_fields()`.

**Rationale**: Currently each function receives the raw XML string and re-parses it. Passing a parsed tree avoids double-parsing and makes the code cleaner.

**Alternative considered**: Keep the current string-based approach with improved regex — rejected because it doesn't solve the fundamental fragility.

### Decision 3: Fallback to "Attributes" tab when tab_structure is empty

**Choice**: In `group_attributes_by_tabs()`, when `tab_structure` is empty, group all fields into a single "Attributes" tab (this is already the current behavior at line 178, but the gate at line 506 prevents it from being reached).

**Rationale**: The current code at line 506 (`if features and tab_structure:`) means that when `tab_structure` is empty, `feature_tabs` stays as `[]` and no structured output is produced. Moving the fallback inside `group_attributes_by_tabs()` and always calling it ensures there's always output.

### Decision 4: Support multiple QGIS XML formats for ExternalResource detection

**Choice**: Check for `ExternalResource` widget type AND `DocumentViewer` as independent attributes within the `<config>` block, rather than requiring a specific substring match.

**Rationale**: The `DocumentViewer` attribute can appear as `name="DocumentViewer"` with `value="1"` anywhere in the Option element. Checking that both exist within the same `<editWidget type="ExternalResource">` block is sufficient.

## Risks / Trade-offs

- **Risk**: QGIS future versions could change the XML structure entirely (e.g., rename `<attributeEditorContainer>`) → **Mitigation**: The XML parser gracefully returns empty results; the fallback path shows all fields. No crash.
- **Risk**: The .qgs file could be malformed or not a valid ZIP → **Mitigation**: `_read_qgs_from_qgz()` already handles this with try/except, returning None. The existing fallback paths handle None gracefully.
- **Trade-off**: Using `xml.etree.ElementTree` means we can't use XPath with namespace prefixes easily → **Mitigation**: The QGS XML uses namespace-free tags for the elements we care about (`attributeEditorContainer`, `attributeEditorField`, `field`, `editWidget`, `config`, `Option`). We can use simple `find()`/`findall()` without namespace handling.
