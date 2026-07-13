import os
from .base import *

DEBUG = True

_db_name = os.environ.get("DJANGO_DB_NAME", str(BASE_DIR / "db.sqlite3"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _db_name,
    }
}
