from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.audit.models import AuditLog
from georidge_platform.apps.qgis_server.services import health_check


@staff_member_required
def index(request):
    qs = Project.objects.filter(tenant=request.tenant) if request.tenant else Project.objects.all()
    total_projects = qs.count()
    published_projects = qs.filter(status=Project.Status.PUBLISHED).count()
    failed_validations = qs.filter(status=Project.Status.FAILED).count()
    draft_projects = qs.filter(status=Project.Status.DRAFT).count()
    server_status = health_check()

    audit_qs = AuditLog.objects.select_related("user", "project")
    if request.tenant:
        audit_qs = audit_qs.filter(project__tenant=request.tenant)
    recent_activity = audit_qs[:20]

    return render(request, "monitoring/index.html", {
        "total_projects": total_projects,
        "published_projects": published_projects,
        "failed_validations": failed_validations,
        "draft_projects": draft_projects,
        "server_status": server_status,
        "recent_activity": recent_activity,
    })
