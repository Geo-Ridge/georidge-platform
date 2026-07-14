## 1. Rewrite QGS XML Parsers

- [x] 1.1 Rewrite `parse_qgs_tab_structure()` in `views.py` to use `xml.etree.ElementTree` — find all `<attributeEditorContainer>` elements with `type="Tab"` attribute (regardless of order), extract `name` attribute, and collect nested `<attributeEditorField name="...">` elements
- [x] 1.2 Rewrite `parse_qgs_external_resource_fields()` in `views.py` to use `xml.etree.ElementTree` — find all `<field>` elements containing `<editWidget type="ExternalResource">` with a nested `<Option name="DocumentViewer" ... value="1"/>` (check `name` and `value` attributes independently)
- [x] 1.3 Update `identify_view()` to pass parsed XML tree (or re-use a single parse) to both functions instead of raw string, or keep string interface if cleaner

## 2. Fix Feature Tabs Fallback

- [x] 2.1 Remove the `tab_structure` gate at `identify_view()` line 506 — always call `group_attributes_by_tabs()` when features are present, so the existing fallback at `group_attributes_by_tabs()` line 178 (single "Attributes" tab) is reached when tab_structure is empty
- [x] 2.2 Verify that `feature_tabs_json` is still serialized correctly to the template when feature_tabs is a single "Attributes" tab

## 3. Verify with Test Projects

- [ ] 3.1 Test with Chenango_County project (old attribute ordering) — confirm tabs and images still display correctly
- [ ] 3.2 Test with img project (QGIS 3.40 alphabetical attribute ordering) — confirm tabs ("Main", "Images") and image field are now detected and displayed
- [ ] 3.3 Test with a project that has no attributeEditorForm — confirm flat field list fallback works
