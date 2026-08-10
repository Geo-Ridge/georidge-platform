import os
import shutil
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from georidge_platform.apps.audit.services import log_action
from georidge_platform.apps.core.utils import hx_redirect

from .forms import ProjectReplaceForm, ProjectUploadForm
from .models import Project
from .services import (
    action_perms,
    project_history,
    publish_project,
    reactivate_project,
    unpublish_project,
)

PROJECT_STATUSES = Project.Status.choices


_BLOCKED_EXTENSIONS = frozenset({'.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.pif', '.vbs', '.js', '.wsh', '.wsf', '.ps1', '.sh', '.bash', '.csh', '.py'})


def _validate_zip_member(member_path):
    ext = os.path.splitext(member_path)[1].lower()
    if ext in _BLOCKED_EXTENSIONS:
        raise ValueError(f"ZIP contains blocked file type: {ext}")


def _handle_zip_upload(project, uploaded_file):
    dest_dir = os.path.join(settings.MEDIA_ROOT, "projects", str(project.pk))
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(uploaded_file) as zf:
        for member in zf.namelist():
            member_path = os.path.normpath(member)
            if member_path.startswith("..") or os.path.isabs(member_path):
                raise ValueError("Invalid ZIP entry path")
            target = os.path.join(dest_dir, member_path)
            target = os.path.normpath(target)
            if not target.startswith(dest_dir):
                raise ValueError("ZIP entry escapes target directory")
            if member.endswith("/"):
                os.makedirs(target, exist_ok=True)
            else:
                _validate_zip_member(member_path)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    qgz_files = [f for f in os.listdir(dest_dir) if f.lower().endswith(".qgz")]
    if not qgz_files:
        raise ValueError("ZIP did not contain a .qgz project file")
    qgz_name = qgz_files[0]
    project.file.name = f"projects/{project.pk}/{qgz_name}"
    project.save(update_fields=["file"])


def _project_scope(request):
    if request.tenant:
        return {"tenant": request.tenant}
    return {}


def _redirect_tenant(to, request, *args, **kwargs):
    url = reverse(to, args=args, kwargs=kwargs)
    return redirect(request.tenant_base + url)


@login_required
def upload(request):
    if request.method == "POST":
        form = ProjectUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            ext = os.path.splitext(uploaded_file.name)[1].lower()

            project = form.save(commit=False)
            project.owner = request.user
            if request.tenant:
                project.tenant = request.tenant

            if ext == ".zip":
                project.file = None
                project.save()
                _handle_zip_upload(project, uploaded_file)
            else:
                project.file = None
                project.save()
                project.file.save(uploaded_file.name, uploaded_file)

            if request.headers.get("HX-Request"):
                return hx_redirect(request.tenant_base + reverse("projects:detail", kwargs={"pk": project.pk}))
            return _redirect_tenant("projects:detail", request, pk=project.pk)
        if request.headers.get("HX-Request"):
            return render(request, "projects/__form.html", {"form": form})
    else:
        form = ProjectUploadForm()
    return render(request, "projects/upload.html", {"form": form})


@login_required
def detail(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    return render(request, "projects/detail.html", {
        "project": project,
        "perms": action_perms(request.user, project),
        "history": project_history(project),
    })


@login_required
def list_view(request):
    qs = Project.objects.filter(**_project_scope(request))
    status_filter = request.GET.get("status", "")
    search = request.GET.get("q", "")
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(name__icontains=search)
    paginator = Paginator(qs, 15)
    page = request.GET.get("page", 1)
    projects_page = paginator.get_page(page)
    return render(request, "projects/list.html", {
        "projects": projects_page,
        "status_filter": status_filter,
        "search": search,
        "project_statuses": PROJECT_STATUSES,
    })


@login_required
def delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    if project.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Permission denied.")
    if request.method == "POST":
        # project.delete() fires the projects.signals.delete_project_files
        # post_delete receiver, which removes the media directory on disk.
        project.delete()
        if request.headers.get("HX-Request"):
            return hx_redirect(request.tenant_base + reverse("projects:list"))
        return _redirect_tenant("projects:list", request)
    if request.headers.get("HX-Request"):
        return render(request, "projects/__confirm_delete.html", {"project": project})
    return render(request, "projects/confirm_delete.html", {"project": project})


@login_required
def publish_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    if not request.user.can_publish():
        return HttpResponseForbidden("Permission denied.")
    try:
        urls = publish_project(project, request.user)
        if request.headers.get("HX-Request"):
            return render(request, "projects/_publish_result.html", {
                "urls": urls,
                "success": True,
                "project": project,
                "perms": action_perms(request.user, project),
                "history": project_history(project),
            })
        return JsonResponse({"success": True, "urls": urls})
    except ValueError as e:
        if request.headers.get("HX-Request"):
            return render(request, "projects/_publish_result.html", {
                "success": False,
                "error": str(e),
                "project": project,
                "perms": action_perms(request.user, project),
                "history": project_history(project),
            })
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
def unpublish_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    if not request.user.can_publish():
        return HttpResponseForbidden("Permission denied.")
    unpublish_project(project, request.user)
    if request.headers.get("HX-Request"):
        return render(request, "projects/_publish_result.html", {
            "success": True,
            "unpublished": True,
            "project": project,
            "perms": action_perms(request.user, project),
            "history": project_history(project),
        })
    return JsonResponse({"success": True})


@login_required
def reactivate_view(request, pk):
    """Re-activate an archived project back to Ready (publisher/admin only)."""
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    if not request.user.can_publish():
        return HttpResponseForbidden("Permission denied.")
    try:
        reactivate_project(project, request.user)
    except ValueError as e:
        if request.headers.get("HX-Request"):
            return render(request, "projects/_publish_result.html", {
                "success": False,
                "error": str(e),
                "project": project,
                "perms": action_perms(request.user, project),
                "history": project_history(project),
            })
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    if request.headers.get("HX-Request"):
        return render(request, "projects/_publish_result.html", {
            "success": True,
            "reactivated": True,
            "project": project,
            "perms": action_perms(request.user, project),
            "history": project_history(project),
        })
    return JsonResponse({"success": True})


@login_required
def replace_file_view(request, pk):
    """Replace the .qgz for an existing project.

    Reuses the same project row: version bumps, publish fields clear, and the
    status resets to Draft (auto-unpublish) so the project must be validated
    and published again. Allowed for the owner and upload-capable roles.
    """
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    if project.owner_id != request.user.id and not request.user.can_upload():
        return HttpResponseForbidden("Permission denied.")

    if request.method == "POST":
        form = ProjectReplaceForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            old_status = project.status
            try:
                if ext == ".zip":
                    _handle_zip_upload(project, uploaded_file)
                else:
                    project.file.save(uploaded_file.name, uploaded_file)
            except ValueError as e:
                if request.headers.get("HX-Request"):
                    return render(request, "projects/_replace_file.html", {
                        "project": project, "form": form, "error": str(e),
                    })
                return JsonResponse({"success": False, "error": str(e)}, status=400)
            project.version += 1
            project.published_by = None
            project.published_at = None
            project.published_version = None
            project.save(update_fields=[
                "version", "published_by", "published_at", "published_version", "updated_at",
            ])
            project.transition_to(Project.Status.DRAFT)
            log_action(request.user, "file_replaced", project=project, details={
                "from": old_status, "to": "Draft", "version": project.version,
            })
            if request.headers.get("HX-Request"):
                return render(request, "projects/_replace_result.html", {
                    "project": project,
                    "version": project.version,
                    "perms": action_perms(request.user, project),
                    "history": project_history(project),
                })
            return _redirect_tenant("projects:detail", request, pk=project.pk)
        if request.headers.get("HX-Request"):
            return render(request, "projects/_replace_file.html", {
                "project": project, "form": form,
            })
    else:
        form = ProjectReplaceForm()
    return render(request, "projects/_replace_file.html", {
        "project": project, "form": form,
    })
