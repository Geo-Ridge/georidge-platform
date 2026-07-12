import os
from django.core.asgi import get_asgi_application
from georidge_platform.qgis_setup import configure_pyqgis

configure_pyqgis()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "georidge_platform.settings.prod")

application = get_asgi_application()
