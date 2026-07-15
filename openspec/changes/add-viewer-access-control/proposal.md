## Why

Currently the viewer (`view_view` at `viewer/views.py:419`) is fully public within a tenant — no login required, no project status check. Any tenant member can view any project by ID regardless of its workflow status. This means:

- Draft/working projects are exposed to all tenant members and (if URLs leak) the public.
- There is no way to distinguish "team working on a project" from "project ready for public consumption".

We need a model where the project team (owner, editors, admins) can view projects while working on them, but anonymous/public users only see **Published** projects.

## What Changes

- Add access control to `view_view` in `viewer/views.py`:
  - Anonymous users → only `Project.Status.PUBLISHED` projects are viewable.
  - Authenticated users who are **owner** of the project → all statuses (DRAFT, VALIDATING, READY, PUBLISHED, FAILED, ARCHIVED).
  - Authenticated users with role `ADMIN` or `PUBLISHER` → all statuses.
  - Authenticated users with role `EDITOR` → all statuses for projects they can edit (owner or tenant editor).
  - Authenticated users with role `VIEWER` → only `PUBLISHED`.
- Apply the same gate to the supporting viewer endpoints (`wms_proxy_view`, `identify_view`, `search_view`, panel views) to prevent data leakage through those paths.
- Return `403 Forbidden` (or redirect to login for anonymous) when access is denied.

## Capabilities

### New Capabilities
- `viewer-access-control`: Viewer enforces project status + role-based access. Anonymous users see only published projects; authenticated team members can view working drafts.

### Modified Capabilities
(none)

## Impact

- `viewer/views.py` — `view_view` gets `@login_required` + status/role gate; helper `_can_view_project(request, project)` added and reused by `wms_proxy_view`, `identify_view`, `search_view`, and panel views.
- `accounts/models.py` — `User.Role` already has ADMIN/PUBLISHER/EDITOR/VIEWER; may add `can_edit()` helper mirroring `can_publish()`.
- `projects/models.py` — `Project.Status` already defines DRAFT/VALIDATING/READY/PUBLISHED/FAILED/ARCHIVED; no model change needed.
- Templates — `viewer/viewer.html` and error pages may need a "not authorized" state.
- Tests — add tests for each role × status combination.
