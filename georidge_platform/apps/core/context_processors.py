def tenant(request):
    return {
        "tenant": getattr(request, "tenant", None),
        "tenant_slug": getattr(request, "tenant_slug", ""),
        "tenant_base": getattr(request, "tenant_base", ""),
    }
