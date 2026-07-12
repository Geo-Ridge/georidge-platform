import os
from django.core.wsgi import get_wsgi_application
from georidge_platform.qgis_setup import configure_pyqgis

configure_pyqgis()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "georidge_platform.settings.prod")

application = get_wsgi_application()
