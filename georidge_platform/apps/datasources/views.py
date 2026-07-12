from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ConnectionProfile


@login_required
def list_view(request):
    qs = ConnectionProfile.objects.filter(tenant=request.tenant) if request.tenant else ConnectionProfile.objects.all()
    return render(request, "datasources/list.html", {"profiles": qs})
