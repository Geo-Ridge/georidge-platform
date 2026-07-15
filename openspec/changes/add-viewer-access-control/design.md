## Context

The viewer is currently an open endpoint within a tenant. There is no notion of "who can see this project in what state." The `Project.Status` field exists and drives the admin validation/publish workflow, but it is never consulted by the viewer.

Roles already exist on `User` (`ADMIN`, `PUBLISHER`, `EDITOR`, `VIEWER`) with helpers `can_publish()` and `can_upload()`. `Project` has an `owner` FK.

## Decision

Implement **Option D** (hybrid gate):

```
def _can_view_project(request, project):
    # Published is always visible (incl. anonymous)
    if project.status == Project.Status.PUBLISHED:
        return True
    # Must be logged in for anything else
    if not request.user.is_authenticated:
        return False
    user = request.user
    # Owner always allowed
    if project.owner_id == user.pk:
        return True
    # Tenant admins / publishers see everything
    if user.role in (User.Role.ADMIN, User.Role.PUBLISHER):
        return True
    # Editors see drafts they can work on
    if user.role == User.Role.EDITOR and user.tenant_id == project.tenant_id:
        return True
    # Viewers and others: only published (already handled above)
    return False
```

### Endpoint coverage
- `view_view` (`viewer/views.py:419`): add `@login_required` + gate. Anonymous denied → redirect to login (Django default) or `403`.
- `wms_proxy_view` (`viewer/views.py:395`): gate before proxying WMS tiles.
- `identify_view` (`viewer/views.py:441`): gate before GetFeatureInfo.
- `search_view` (`viewer/views.py:329`): gate before WFS search.
- Panel views (`legend_panel`, `layers_panel`): gate (they already require `@login_required`).

### ARCHIVED handling
ARCHIVED means "was published, now taken down." Treat it like non-published: owner/admin/publisher/editor can view, anonymous/viewers cannot. (Follows the table from exploration.)

### Error experience
- Anonymous hitting a non-published project → `403` or redirect to login. Simpler: return `HttpResponseForbidden` with a minimal template, or redirect to `accounts:login` with `next` param.
- Authenticated but lacking permission → `403`.

## Risks / Open Questions
- **Embed/iframe**: `view_view` is `@xframe_options_exempt` for embedding. Public embeds of published projects still work. Embeds of drafts will now require auth — acceptable.
- **Tenant isolation**: `_project_scope` already scopes by tenant; gate is applied after fetch, so cross-tenant is already blocked.
- **Performance**: gate is a simple attribute check + one FK compare; negligible.
- **Existing bookmarks**: any saved draft URLs will start returning 403 for anonymous users — expected behavior change, communicate to users.
