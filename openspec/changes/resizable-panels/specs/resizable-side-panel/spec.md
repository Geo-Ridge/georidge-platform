## ADDED Requirements

### Requirement: Side panel is resizable via drag handle
Each layout's main side panel (layers + feature info tabs) SHALL have an invisible resize handle on its right edge that allows users to drag and resize the panel width.

#### Scenario: Resize handle visible on hover
- **WHEN** user hovers over the right edge (6px zone) of the side panel
- **THEN** cursor changes to `col-resize`

#### Scenario: Drag handle to resize
- **WHEN** user presses pointerdown on the resize handle and drags horizontally
- **THEN** panel width updates in real-time to follow the pointer position

#### Scenario: Width clamped to minimum
- **WHEN** user drags the panel narrower than 200px
- **THEN** panel width is clamped to 200px

#### Scenario: Width clamped to maximum
- **WHEN** user drags the panel wider than 50% of the viewport width
- **THEN** panel width is clamped to 50% of the viewport width

### Requirement: MapGuide map adjusts to panel width
In MapGuide layout, the map SHALL automatically adjust its width when the side panel is resized, since the panel is a flex child.

#### Scenario: Map shrinks when panel grows
- **WHEN** user drags the MapGuide panel wider
- **THEN** the map flex-shrinks to accommodate the wider panel

#### Scenario: Map grows when panel shrinks
- **WHEN** user drags the MapGuide panel narrower
- **THEN** the map flex-grows to fill the freed space

### Requirement: Map viewport recalculated after resize
The OpenLayers map SHALL recalculate its viewport after a panel resize completes.

#### Scenario: Map updates after resize
- **WHEN** user releases the pointer after resizing a panel
- **THEN** `map.updateSize()` is called so the map renders correctly at the new size

### Requirement: Transition disabled during drag
The panel CSS transition SHALL be temporarily disabled during a resize drag for precise, lag-free feedback.

#### Scenario: No transition during drag
- **WHEN** user is actively dragging the resize handle
- **THEN** panel width changes instantly (no 0.2s ease transition)

#### Scenario: Transition restored after drag
- **WHEN** user releases the pointer after resizing
- **THEN** the original CSS transition is restored
