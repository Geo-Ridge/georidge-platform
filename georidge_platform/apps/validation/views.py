import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from georidge_platform.apps.projects.models import Project
from .services import validate_project


def _project_scope(request):
    if request.tenant:
        return {"tenant": request.tenant}
    return {}


@login_required
def validate_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    report = validate_project(project.file.path, project=project)
    if not report.valid:
        project.status = Project.Status.FAILED
    else:
        project.status = Project.Status.READY
    project.save(update_fields=["status"])
    data = report.to_dict()
    data["project_status"] = project.status
    if request.headers.get("HX-Request"):
        from django.shortcuts import render
        return render(request, "projects/_validation_result.html", {
            "report": report,
            "project": project,
        })
    return JsonResponse(data)
