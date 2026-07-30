import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "georidge_platform.settings.dev")

application = get_wsgi_application()

from georidge_platform.startup import run_startup

run_startup()
