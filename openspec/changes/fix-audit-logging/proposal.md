## Why

The audit logging system exists but is effectively non-functional. Only 3 actions are logged (login, publish, unpublish), there's no tenant field so entries without a project are invisible in tenant-scoped views, and the `/audit/` URL itself 404s because the tenancy middleware interprets it as a tenant slug.

## What Changes

- Add `tenant` field to `AuditLog` model (new migration)
- Update `log_action()` to accept and store tenant
- Add `/audit/` to `NO_TENANT_PREFIXES` so the URL resolves
- Fix audit trail view to show entries without a project (login/logout) regardless of tenant filter
- Add Django signals in audit app to auto-log admin CRUD actions on Project, User, and AuditLog itself
- Add logout logging

## Capabilities

### New Capabilities
- `audit-auto-logging`: Django signals that automatically log admin CRUD actions (create, update, delete) on key models
- `audit-tenant-fix`: Tenant field on AuditLog and proper filtering so all entries are visible

### Modified Capabilities
(none)

## Impact

- `georidge_platform/apps/audit/models.py` — add `tenant` field
- `georidge_platform/apps/audit/services.py` — accept tenant param
- `georidge_platform/apps/audit/views.py` — fix filtering logic
- `georidge_platform/apps/audit/signals.py` — new file, signal receivers
- `georidge_platform/apps/audit/apps.py` — register signals in `ready()`
- `georidge_platform/apps/core/middleware.py` — add `/audit/` to prefixes
- `georidge_platform/apps/accounts/views.py` — add logout logging
- New migration for tenant field
