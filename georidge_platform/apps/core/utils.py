def tenant_redirect(to, request, *args, **kwargs):
    from django.shortcuts import redirect
    from django.urls import reverse
    url = reverse(to, args=args, kwargs=kwargs)
    return redirect(request.tenant_base + url)


def hx_redirect(url):
    from django.http import HttpResponse
    response = HttpResponse()
    response["HX-Redirect"] = url
    return response
