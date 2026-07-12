## 1. Update identify-manager.js event dispatch

- [x] 1.1 Pass `featureTabs` and `qgisHtml` in the `identify-complete` event detail

## 2. Update identify-popup.js event handling

- [x] 2.1 Use pre-parsed `featureTabs` from event detail in `showPopup`
- [x] 2.2 Use pre-parsed `qgisHtml` from event detail as fallback
- [x] 2.3 Remove redundant regex parsing of `data-feature-tabs` and `data-qgis-html` from HTML
