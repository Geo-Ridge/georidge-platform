from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import AuditLog


@staff_member_required
def audit_trail(request):
    qs = AuditLog.objects.select_related("user", "project")
    if request.tenant:
        qs = qs.filter(project__tenant=request.tenant)
    logs = qs.all()
    paginator = Paginator(logs, 50)
    page = request.GET.get("page", 1)
    logs_page = paginator.get_page(page)
    return render(request, "audit/list.html", {"logs": logs_page})
