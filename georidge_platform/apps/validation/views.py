from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from georidge_platform.apps.audit.services import log_action
from georidge_platform.apps.projects.models import Project
from .services import validate_project


def _project_scope(request):
    if request.tenant:
        return {"tenant": request.tenant}
    return {}


@login_required
def validate_view(request, pk):
    project = get_object_or_404(Project, pk=pk, **_project_scope(request))
    # Validation is limited to the owner and upload-capable roles (editor,
    # publisher, admin). VIEWERs may test-view but not change status.
    if project.owner_id != request.user.id and not request.user.can_upload():
        return HttpResponseForbidden("Permission denied.")

    old_status = project.status
    try:
        project.transition_to(Project.Status.VALIDATING)
    except ValueError as e:
        if request.headers.get("HX-Request"):
            from django.shortcuts import render
            return render(request, "projects/_validation_result.html", {
                "error": str(e),
                "project": project,
            })
        return JsonResponse({"error": str(e)}, status=400)

    log_action(request.user, "validation_started", request=request, project=project,
               details={"from": old_status, "to": "Validating"})

    try:
        report = validate_project(project.file.path, project=project)
    except Exception as e:  # never leave a project stuck in Validating
        project.transition_to(Project.Status.FAILED)
        log_action(request.user, "validation_completed", request=request, project=project,
                   details={
                       "from": "Validating",
                       "to": project.status,
                       "valid": False,
                       "errors": [f"Validation error: {e}"],
                   })
        if request.headers.get("HX-Request"):
            from django.shortcuts import render
            from georidge_platform.apps.projects.services import action_perms, project_history
            return render(request, "projects/_validation_result.html", {
                "error": f"Validation error: {e}",
                "project": project,
                "perms": action_perms(request.user, project),
                "history": project_history(project),
            })
        return JsonResponse({"error": str(e), "project_status": project.status}, status=500)

    if not report.valid:
        project.transition_to(Project.Status.FAILED)
    else:
        project.transition_to(Project.Status.READY)

    log_action(request.user, "validation_completed", request=request, project=project,
               details={
                   "from": "Validating",
                   "to": project.status,
                   "valid": report.valid,
                   "errors": report.errors[:5],
               })

    data = report.to_dict()
    data["project_status"] = project.status
    if request.headers.get("HX-Request"):
        from django.shortcuts import render
        from georidge_platform.apps.projects.services import action_perms, project_history
        return render(request, "projects/_validation_result.html", {
            "report": report,
            "project": project,
            "perms": action_perms(request.user, project),
            "history": project_history(project),
        })
    return JsonResponse(data)
