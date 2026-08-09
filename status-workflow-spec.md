# Status Workflow — Specification

**Status:** Draft (pre-implementation)
**Date:** 2026-08-09
**Source:** Requirements interview (4 rounds) + codebase analysis

---

## 1. Goal

Implement the **project status workflow** so the lifecycle of a project (Draft → Validating →
Ready/Failed → Published → Archived) is:

1. **Enforced** — transitions and role permissions are rules, not free-form status edits.
2. **Visible** — the project page shows the current status, the actions available at that
   stage, and a compact history of changes.
3. **Honest** — VALIDATING becomes a real in-progress state while validation runs.
4. **Accessible by design** — **Published projects are open to the public**; every other
   status remains **viewable by any logged-in user for testing** (with a clear preview
   banner in the viewer).

---

## 2. Current state (as-is)

| Aspect | Today |
|---|---|
| Statuses | `Draft`, `Validating`, `Ready`, `Published`, `Archived`, `Failed` (all defined in `Project.Status`) |
| VALIDATING | Defined but **never set** — validation jumps DRAFT → READY/FAILED synchronously |
| Validate | `validation/views.py:validate_view` — `@login_required` only, **no role check**; sets READY or FAILED |
| Publish | `projects/services.py:publish_project` — requires READY, role `can_publish()` (ADMIN/PUBLISHER); records `published_by/at/version` |
| Unpublish | `unpublish_project` — sets ARCHIVED, clears publish fields |
| Delete | Owner or superuser (`delete_view`) |
| Viewer access | `add-viewer-access-control`: anonymous → PUBLISHED only; owner/ADMIN/PUBLISHER/EDITOR → all; **VIEWER → PUBLISHED only** |
| History | `AuditLog` exists (`audit.services.log_action`); logs `publish_completed`, `unpublish` only; **not surfaced in UI** |
| Project page | Status badge + Validate/Publish/Unpublish/Delete buttons (buttons not role-gated in the template) |
| List page | Status filter dropdown + colored badges |
| Version | `version` (default 1), `published_version` recorded at publish |

Tests: `integration/tests/test_workflow.py` covers upload→Draft, publish-requires-validation,
role enforcement for publish, delete ownership.

---

## 3. Requirements

### 3.1 Visibility model (core)
- **PUBLISHED** projects are open to the public (anonymous users, current behavior).
- **All other statuses** (DRAFT, VALIDATING, READY, FAILED, ARCHIVED) are viewable by
  **any logged-in user** of the tenant — including the `VIEWER` role — **for testing**.
  - ⚠️ This **changes** the current `add-viewer-access-control` rule that restricted
    `VIEWER` to published projects only. The viewer gate must be relaxed accordingly.

### 3.2 Viewer preview banner
- The map viewer shows a **banner on every non-published project**: **"Draft for testing only"**.
- Warnings/styling: amber/warning-tinted bar; must not block map interaction.
- Applies to DRAFT, VALIDATING, READY, FAILED, ARCHIVED.
- No in-map banner for PUBLISHED (clean public view).

### 3.3 Statuses and allowed transitions
`VALIDATING` is now a **real in-progress state** set while a validation runs, then resolved
to READY or FAILED.

| From | To | Action |
|---|---|---|
| DRAFT | VALIDATING | Validate |
| FAILED | VALIDATING | Re-validate (recovery path) |
| VALIDATING | READY | Validation passes |
| VALIDATING | FAILED | Validation fails |
| READY | PUBLISHED | Publish |
| PUBLISHED | ARCHIVED | Unpublish |
| ARCHIVED | READY | Re-activate (no re-validation required) |
| PUBLISHED (or any) | DRAFT | New/updated `.qgz` file uploaded (auto-unpublish) |

Notes:
- READY → DRAFT is not a legal transition except via new file upload.
- All transitions must be enforced centrally (model method or service) so no caller can
  set an arbitrary status. `ValueError` on illegal transitions.

### 3.4 Role permissions

| Action | Roles |
|---|---|
| Validate | Owner, EDITOR, PUBLISHER, ADMIN (owner always) |
| Publish | PUBLISHER, ADMIN |
| Unpublish | PUBLISHER, ADMIN |
| Re-activate (ARCHIVED → READY) | PUBLISHER, ADMIN |
| Delete | Owner, ADMIN |
| Replace file (new version) | Owner, EDITOR, PUBLISHER, ADMIN |
| Upload new project | Any logged-in user (current) |
| View non-published (test) | Any logged-in user |
| View published (public) | Anonymous + everyone |

### 3.5 Project detail page layout
Keep the current layout, enhanced:
1. **Status badge** (existing, colored).
2. **Contextual action buttons** — only the legal next actions for the current status,
   and only if the user has the role (hide/disable buttons the user can't perform).
3. **Compact history list** below the actions — status changes and key events, newest
   first: action label, user, timestamp (e.g. "Published by x@y at 2026-08-09 14:32").
   Data source: `AuditLog` filtered by project.

### 3.6 History / audit logging
Log every workflow event with from→to in `details`:
- `upload_created` (project → DRAFT)
- `validation_started` (→ VALIDATING)
- `validation_completed` (→ READY or FAILED, with error summary in details)
- `publish_completed` (→ PUBLISHED)
- `unpublish` (→ ARCHIVED)
- `reactivate` (→ READY)
- `file_replaced` (→ DRAFT, new version)

### 3.7 Versioning
- `version` increments by 1 on **each new .qgz file upload/replacement** (1, 2, 3…).
- `published_version` records which version was published (existing field, preserved).

---

## 4. Behavior details & edge cases

- **Re-activate (ARCHIVED → READY)** skips re-validation (per decision). The Publish
  button becomes available again at READY.
- **Validation while VALIDATING**: the in-progress state is set for the duration of the
  (synchronous) request; the response renders READY/FAILED. For the UI this may flash —
  acceptable, but the history list will show both `validation_started` and
  `validation_completed`.
- **FAILED details**: validation errors/warnings are visible to **owner + any logged-in
  user** (team testers can open and see them).
- **New file on published project**: auto-unpublishes → DRAFT, bumps version, clears
  publish fields (published_by/at/version), and the public viewer immediately stops
  serving it (status gate).
- **Delete** any status (owner/admin), including PUBLISHED — existing behavior; media
  cleanup signal already in place.
- **List page**: existing status filter + badges remain; no new list UI planned.

---

## 5. Proposed change map (for implementation, not yet done)

- `projects/models.py` — central transition API, e.g. `Project.transition_to(new_status, user)` with a transition table + `clean()`/validation; version bump helper on file replace.
- `projects/services.py` — `reactivate_project()`; extend `publish/unpublish` to use the transition API; log all events (validation, reactivate, file replaced).
- `projects/views.py` — new `reactivate_view`; role checks on `validate`/`publish`/`unpublish`/`delete`; expose history list in `detail` context (from `AuditLog`); `upload` — treat new file for an existing published project (replace flow) vs. new project (TBD, see open questions).
- `validation/views.py` — set VALIDATING before running, READY/FAILED after; enforce validate role; log started/completed.
- `viewer/views.py` + `viewer/services.py` — relax access gate so any logged-in user can view non-published; pass `is_preview`/status to the viewer page context.
- Viewer layouts (5) + `map-core.js`/shared partial — render the **"Draft for testing only"** banner when status != PUBLISHED.
- `templates/projects/detail.html` — contextual action buttons + compact history list; role-gate buttons.
- Tests — extend `test_workflow.py`: transition rules, role matrix per action, history entries, banner presence by status, viewer access for VIEWER role on drafts, auto-unpublish on file replace.

---

## 6. Open questions / to confirm during implementation

1. **"New file upload" flow**: today every upload creates a *new* project. Does "replace
   file on a published project" mean (a) a new "Replace file" action on the project page
   that reuses the same project row (version bump, → DRAFT), or (b) re-uploading creates a
   new project and the old one should be archived? Spec assumes (a) but needs confirmation.
2. **Banner text**: fixed "Draft for testing only" for all non-published statuses, or
   status-specific copy (e.g. "Validation failed")? Interview chose fixed text; flagged in
   case testing shows otherwise.
3. **Re-activate without re-validation**: confirmed as a decision, but re-validation may be
   desirable for safety on production data — revisit if the team prefers.
4. **VIEWER role relaxation**: relaxing VIEWER to see drafts contradicts the earlier
   `add-viewer-access-control` spec — confirm this is the intended new policy.
5. **Upload permission**: currently any logged-in user can upload; restrict to
   owner/EDITOR/PUBLISHER/ADMIN? (left as current in this spec).
