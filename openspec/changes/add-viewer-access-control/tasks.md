## 1. Add access-control helper
- [ ] Add `_can_view_project(request, project)` to `viewer/views.py` implementing the Option D gate (published = public; owner/admin/publisher/editor = all; viewer/anonymous = published only).

## 2. Gate the main viewer endpoint
- [ ] Add `@login_required` to `view_view` (`viewer/views.py:419`).
- [ ] Call `_can_view_project` after `get_object_or_404`; return `403 Forbidden` (or redirect to login for anonymous) when denied.

## 3. Gate supporting viewer endpoints
- [ ] Apply `_can_view_project` to `wms_proxy_view` (`viewer/views.py:395`) before proxying.
- [ ] Apply `_can_view_project` to `identify_view` (`viewer/views.py:441`) before GetFeatureInfo.
- [ ] Apply `_can_view_project` to `search_view` (`viewer/views.py:329`) before WFS query.
- [ ] Confirm panel views (`legend_panel`, `layers_panel`) are covered by existing `@login_required` + gate.

## 4. Account helper (optional but recommended)
- [ ] Add `User.can_edit()` helper mirroring `can_publish()` if editor logic needs reuse.

## 5. Error / unauthorized UX
- [ ] Add a minimal "not authorized" response/template for `403` from viewer endpoints.
- [ ] Ensure anonymous → non-published redirect goes to login with `next` param (or clear 403).

## 6. Tests
- [ ] Add tests covering each role (anonymous, VIEWER, EDITOR, PUBLISHER, ADMIN, owner) × status (DRAFT, READY, PUBLISHED, ARCHIVED) matrix for `view_view`.
- [ ] Add tests for `wms_proxy_view`, `identify_view`, `search_view` gating.
- [ ] Verify published projects remain publicly embeddable (iframe still works).

## 7. Verify & document
- [ ] Run lint/typecheck.
- [ ] Document the access model in admin/help or README note.
