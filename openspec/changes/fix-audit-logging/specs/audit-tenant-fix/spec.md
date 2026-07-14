## ADDED Requirements

### Requirement: AuditLog has tenant field
The AuditLog model SHALL have a nullable ForeignKey to Tenant.

#### Scenario: AuditLog entry with project
- **WHEN** an audit entry is created for a project action
- **THEN** the tenant field is populated from the project's tenant

#### Scenario: AuditLog entry without project
- **WHEN** an audit entry is created for a non-project action (login, logout)
- **THEN** the tenant field is null

### Requirement: /audit/ URL is accessible
The `/audit/` URL SHALL resolve without requiring a tenant prefix.

#### Scenario: Staff user访问 /audit/
- **WHEN** a staff user navigates to `/audit/`
- **THEN** the audit trail page loads (not a 404)

### Requirement: Audit trail shows all entries globally
The audit trail view SHALL show all audit entries when accessed without a tenant prefix.

#### Scenario: Global audit trail
- **WHEN** a staff user visits `/audit/` (no tenant in URL)
- **THEN** all AuditLog entries are displayed, including those with null project

#### Scenario: Tenant-scoped audit trail
- **WHEN** a staff user visits `/<tenant>/audit/` (tenant in URL)
- **THEN** only entries where `project__tenant` matches OR `tenant` field matches are shown

### Requirement: log_action accepts tenant
The `log_action()` service function SHALL accept an optional `tenant` parameter.

#### Scenario: log_action with tenant
- **WHEN** `log_action()` is called with `tenant=some_tenant`
- **THEN** the created AuditLog entry has the tenant field set

#### Scenario: log_action without tenant
- **WHEN** `log_action()` is called without a tenant argument
- **THEN** the tenant field is null on the created entry
