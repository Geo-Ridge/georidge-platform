## ADDED Requirements

### Requirement: Identify popup is resizable via drag handle
The floating identify popup SHALL have an invisible resize handle on its right edge that allows users to drag and resize the popup width.

#### Scenario: Resize handle visible on hover
- **WHEN** user hovers over the right edge (6px zone) of the identify popup
- **THEN** cursor changes to `col-resize`

#### Scenario: Drag handle to resize
- **WHEN** user presses pointerdown on the resize handle and drags horizontally
- **THEN** popup width updates in real-time to follow the pointer position

#### Scenario: Width clamped to minimum
- **WHEN** user drags the popup narrower than 200px
- **THEN** popup width is clamped to 200px

#### Scenario: Width clamped to maximum
- **WHEN** user drags the popup wider than 50% of the viewport width
- **THEN** popup width is clamped to 50% of the viewport width

### Requirement: Popup drag-to-move preserved
The popup header drag-to-move functionality SHALL continue to work alongside the new resize handle.

#### Scenario: Header drag moves popup
- **WHEN** user presses pointerdown on the popup header (outside the resize handle zone)
- **THEN** popup can be dragged to a new position

#### Scenario: Right edge drag resizes popup
- **WHEN** user presses pointerdown on the right 6px edge of the popup
- **THEN** popup is resized (not moved)

### Requirement: Popup position adjusts for new width
The popup position calculation SHALL account for the actual popup width, not a hardcoded value.

#### Scenario: Popup stays on screen after resize
- **WHEN** the popup is resized wider and then a new identify is triggered
- **THEN** the popup is positioned so it does not overflow the right edge of the viewport
