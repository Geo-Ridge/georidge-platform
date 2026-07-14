from django.contrib.auth import login, logout
from django.shortcuts import render, redirect

from .forms import LoginForm
from georidge_platform.apps.audit.services import log_action
from georidge_platform.apps.core.utils import hx_redirect


def _dashboard_url(request):
    return "/admin/"


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_url(request))
    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_action(user, "login", request=request)
        url = _dashboard_url(request)
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
