from django.http import Http404
from georidge_platform.apps.accounts.models import Tenant

NO_TENANT_PREFIXES = ("/admin/", "/static/", "/media/", "/accounts/")


class TenancyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if path == "/" or any(path.startswith(p) for p in NO_TENANT_PREFIXES):
            request.tenant = None
            request.tenant_slug = ""
            request.tenant_base = ""
            return self.get_response(request)

        parts = path.split("/")
        if len(parts) >= 2 and parts[1]:
            slug = parts[1]
            try:
                request.tenant = Tenant.objects.get(slug=slug)
                request.tenant_slug = slug
                request.tenant_base = f"/{slug}"
                new_path = "/" + "/".join(parts[2:])
                request.path_info = new_path
                request.path = new_path
            except Tenant.DoesNotExist:
                raise Http404("Tenant not found")
        else:
            raise Http404("Tenant not found")

        return self.get_response(request)
