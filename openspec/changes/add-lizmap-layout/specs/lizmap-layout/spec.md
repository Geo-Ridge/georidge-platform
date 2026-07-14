## ADDED Requirements

### Requirement: Lizmap layout preset available
The system shall support a `lizmap` layout preset that renders a left icon sidebar with a tabbed dock panel.

#### Scenario: Theme uses lizmap layout
- **WHEN** a project's theme has `layout_preset = "lizmap"`
- **THEN** the viewer renders the lizmap layout template
- **AND** the layout shows a 48px left icon sidebar with tool buttons
- **AND** a tabbed dock panel with Layers and Feature Info tabs

### Requirement: Left icon sidebar
The lizmap layout shall have a vertical icon sidebar on the left with:
- Tool buttons: Identify, Zoom In, Zoom Out, Zoom Rectangle, Full Extent, Measure Distance, Measure Area, Clear, Print
- Active tool is highlighted
- Sidebar uses theme CSS variables for colors

#### Scenario: Tool button interaction
- **WHEN** user clicks a tool button
- **THEN** the tool activates (same behavior as other layouts)
- **AND** the button shows active state

### Requirement: Tabbed dock panel
The dock panel shall have two tabs: Layers and Feature Info.

#### Scenario: Switching tabs
- **WHEN** user clicks a tab
- **THEN** the corresponding content panel becomes visible
- **AND** the other panels are hidden

#### Scenario: Layers tab
- **WHEN** the Layers tab is active
- **THEN** the layer tree is displayed (rendered by layer-manager.js)

#### Scenario: Feature Info tab
- **WHEN** the Feature Info tab is active
- **THEN** the feature info content area is displayed
- **AND** clicking the map shows identified features in this area

### Requirement: Dock panel is resizable
The dock panel width shall be adjustable via drag handle (reusing panel-resize.js).

### Requirement: Lizmap Classic theme seeded
The system shall include a "Lizmap Classic" theme in DEFAULT_THEMES with:
- Blue primary (#1a73e8), white background
- layout_preset = "lizmap"
- show_toolbar = True, show_legend = True, show_statusbar = True, show_banner = True
- Banner: blue (#013466) background, white text, "Lizmap Classic" title
