from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from georidge_platform.apps.audit.services import log_action
from georidge_platform.apps.core.utils import hx_redirect

from .forms import LoginForm


def _dashboard_url(request):
    return "/admin/"


def _safe_next(request):
    """Return the ?next= target only if it is a same-site absolute path."""
    next_url = request.GET.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return ""


def login_view(request):
    next_url = _safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or _dashboard_url(request))
    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_action(user, "login", request=request)
        url = next_url or _dashboard_url(request)
        if request.headers.get("HX-Request"):
            return hx_redirect(url)
        return redirect(url)
    if request.method == "POST" and request.headers.get("HX-Request"):
        return render(request, "accounts/__login_form.html", {"form": form})
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if request.method == "GET":
        return render(request, "accounts/logout.html")
    log_action(request.user, "logout", request=request)
    logout(request)
    return redirect("/accounts/login/")
