## Context

The audit system has a model (`AuditLog`), a service (`log_action()`), a view, admin, and templates — but almost nothing feeds into it. Only 3 explicit `log_action()` calls exist. The model has no tenant field, so entries without a project (like logins) are invisible in tenant-scoped views. The `/audit/` URL 404s because the tenancy middleware treats it as a tenant slug.

## Goals / Non-Goals

**Goals:**
- Make `/audit/` accessible (add to `NO_TENANT_PREFIXES`)
- Add `tenant` field to `AuditLog` so entries are properly scoped
- Auto-log admin CRUD actions via Django signals (Project, User)
- Log logout events
- Fix audit trail view to show all entries (not just project-scoped ones)

**Non-Goals:**
- No middleware-based audit logging (too broad, captures reads)
- No audit logging for viewer/API read operations
- No audit log export or reporting beyond existing views

## Decisions

### 1. Django signals for auto-logging

Use `post_save` and `post_delete` signals on `Project` and `User` models. The `AuditConfig.ready()` method registers receivers. This covers admin CRUD without manually adding `log_action()` calls everywhere.

**Alternatives considered:**
- Admin `log_change()` / `log_addition()` / `log_deletion()` — Django's built-in admin logging uses `django.contrib.admin.models.LogEntry`, which is a separate system. We'd be duplicating. Also doesn't capture non-admin edits.
- Audit middleware — captures too much (reads, static files). Signals are targeted.

### 2. Tenant derived from request, not from project

When logging via signals, there's no `request` object. For admin actions, the tenant can be inferred from the project's tenant. For login/logout, `request.tenant` is None (accounts is in `NO_TENANT_PREFIXES`), so tenant is stored as None — these entries show in the global audit trail.

### 3. Audit trail view shows all entries when no tenant

When `request.tenant` is None (viewing from `/audit/` without a tenant prefix), show all entries. When a tenant is set, filter by `project__tenant` OR `tenant` field matching.

### 4. Exclude AuditLog from its own signals

The signal receivers must not log changes to `AuditLog` itself to avoid infinite recursion.

## Risks / Trade-offs

- **Signal noise** → Admin saves trigger signals. Some saves are redundant (e.g., auto-saving related models). Mitigated by checking if fields actually changed in `post_save`.
- **Migration required** → Adding `tenant` field to `AuditLog` needs a migration. Non-destructive, backward-compatible (nullable).
- **No request context in signals** → Signal receivers don't have access to `request`. IP address and user must be passed via thread-local or middleware-stored request. Mitigated by using `threading.local()` in the middleware to store the current request.
