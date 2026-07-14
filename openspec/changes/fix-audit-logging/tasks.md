## 1. Model & Migration

- [x] 1.1 Add `tenant` ForeignKey to `AuditLog` model (nullable, SET_NULL)
- [x] 1.2 Create and apply migration for tenant field

## 2. Fix URL & View

- [x] 2.1 Add `/audit/` to `NO_TENANT_PREFIXES` in middleware.py
- [x] 2.2 Update `log_action()` to accept optional `tenant` parameter
- [x] 2.3 Fix audit trail view: show all entries when no tenant, filter by `project__tenant` OR `tenant` when tenant is set

## 3. Thread-local request storage

- [x] 3.1 Add thread-local storage in middleware to make current request accessible to signals
- [x] 3.2 Store request in thread-local at start of middleware, clean up at end

## 4. Signal-based auto-logging

- [x] 4.1 Create `signals.py` with `post_save`/`post_delete` receivers for Project and User
- [x] 4.2 Exclude AuditLog from its own signal receivers
- [x] 4.3 Register signals in `AuditConfig.ready()`

## 5. Logout logging

- [x] 5.1 Add `log_action()` call to `logout_view` in accounts/views.py
