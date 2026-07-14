## ADDED Requirements

### Requirement: Auto-log Project CRUD
The system SHALL automatically log create, update, and delete actions on Project models via Django signals.

#### Scenario: Project created via admin
- **WHEN** a Project is created through the Django admin
- **THEN** an AuditLog entry is created with action "project_created", the project's tenant, and the user from the current request

#### Scenario: Project updated via admin
- **WHEN** a Project is saved through the Django admin (existing object)
- **THEN** an AuditLog entry is created with action "project_updated", the project's tenant, and the user from the current request

#### Scenario: Project deleted via admin
- **WHEN** a Project is deleted through the Django admin
- **THEN** an AuditLog entry is created with action "project_deleted", the project's tenant, and the user from the current request

### Requirement: Auto-log User CRUD
The system SHALL automatically log create, update, and delete actions on User models via Django signals.

#### Scenario: User created
- **WHEN** a User is created
- **THEN** an AuditLog entry is created with action "user_created"

#### Scenario: User updated
- **WHEN** a User is saved (existing object)
- **THEN** an AuditLog entry is created with action "user_updated"

#### Scenario: User deleted
- **WHEN** a User is deleted
- **THEN** an AuditLog entry is created with action "user_deleted"

### Requirement: Log logout events
The system SHALL log user logout actions.

#### Scenario: User logs out
- **WHEN** a user clicks logout and confirms
- **THEN** an AuditLog entry is created with action "logout" and the user reference

### Requirement: No self-logging
The system SHALL NOT create audit log entries for changes to the AuditLog model itself.

#### Scenario: AuditLog entry created
- **WHEN** an AuditLog entry is saved to the database
- **THEN** no signal-triggered audit entry is created for that save
