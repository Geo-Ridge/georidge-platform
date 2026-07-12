import os
from decouple import config, Csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="insecure-dev-key-change-in-production")

DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",

    "georidge_platform.apps.core",
    "georidge_platform.apps.accounts",
    "georidge_platform.apps.datasources",
    "georidge_platform.apps.publishing",
    "georidge_platform.apps.projects",
    "georidge_platform.apps.validation",
    "georidge_platform.apps.qgis_server",
    "georidge_platform.apps.viewer",
    "georidge_platform.apps.permissions",
    "georidge_platform.apps.audit",
    "georidge_platform.apps.monitoring",
    "georidge_platform.apps.integration",
]

AUTH_USER_MODEL = "accounts.User"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "georidge_platform.apps.core.middleware.TenancyMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "georidge_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "georidge_platform.apps.core.context_processors.tenant",
            ],
        },
    },
]

WSGI_APPLICATION = "georidge_platform.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"

# Tenant configuration
DEFAULT_TENANT_SLUG = config("DEFAULT_TENANT_SLUG", default="default")

QGIS_SERVER_URL = config("QGIS_SERVER_URL", default="http://localhost:8080")
QGIS_PYTHON = config("QGIS_PYTHON", default="E:/OSGeo4W/bin/python-qgis-ltr.bat")
QGIS_SERVER_PROJECTS_PATH = config(
    "QGIS_SERVER_PROJECTS_PATH", default=str(BASE_DIR / "qgis_projects")
)

