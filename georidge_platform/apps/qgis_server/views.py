from django.http import JsonResponse
from .services import health_check


def status_view(request):
    return JsonResponse(health_check())
