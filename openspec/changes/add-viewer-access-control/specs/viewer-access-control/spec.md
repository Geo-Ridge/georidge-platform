## ADDED Requirements

### Requirement: Viewer access is gated by project status and user role
The system SHALL enforce an access gate on the viewer so that project visibility depends on both the project's `status` and the requesting user's authentication/role. Published projects MUST be publicly viewable; non-published projects MUST be restricted to the project team.

#### Scenario: Anonymous user views a published project
- **WHEN** an anonymous (unauthenticated) user requests `view_view` for a project with `status = PUBLISHED`
- **THEN** the viewer renders normally (including embed/iframe)

#### Scenario: Anonymous user views a draft project
- **WHEN** an anonymous user requests `view_view` for a project with `status != PUBLISHED` (e.g. DRAFT, READY, FAILED, ARCHIVED)
- **THEN** access is denied (redirect to login or `403 Forbidden`)

#### Scenario: Project owner views any status
- **WHEN** an authenticated user who is the project `owner` requests `view_view` for the project in any status
- **THEN** the viewer renders normally

#### Scenario: Admin or Publisher views any status
- **WHEN** an authenticated user with role `ADMIN` or `PUBLISHER` requests `view_view` for a project in any status
- **THEN** the viewer renders normally

#### Scenario: Editor views tenant projects in any status
- **WHEN** an authenticated user with role `EDITOR` in the same tenant requests `view_view` for a project in any status
- **THEN** the viewer renders normally

#### Scenario: Viewer role sees only published
- **WHEN** an authenticated user with role `VIEWER` requests `view_view` for a project with `status != PUBLISHED`
- **THEN** access is denied (`403 Forbidden`)

### Requirement: Supporting viewer endpoints inherit the same gate
The WMS proxy, identify (GetFeatureInfo), and search (WFS) endpoints SHALL apply the same access gate as `view_view` to prevent data leakage of non-published projects through those paths.

#### Scenario: WMS proxy blocked for anonymous on draft
- **WHEN** an anonymous user requests `wms_proxy_view` for a non-published project
- **THEN** the proxy returns `403 Forbidden` (no tile data leaked)

#### Scenario: Search blocked for anonymous on draft
- **WHEN** an anonymous user requests `search_view` for a non-published project
- **THEN** the search returns an empty result set or `403 Forbidden`

#### Scenario: Identify blocked for anonymous on draft
- **WHEN** an anonymous user requests `identify_view` for a non-published project
- **THEN** the identify returns no feature data or `403 Forbidden`
