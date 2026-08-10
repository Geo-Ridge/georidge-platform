import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import OperationalError


def run_startup():
    print("[startup] Running startup checks...")

    needs_migrate = False
    try:
        get_user_model().objects.exists()
        print("[startup] Database tables exist, skipping migrations")
    except OperationalError:
        print("[startup] Database tables missing, running migrations...")
        needs_migrate = True
    except Exception as e:
        print(f"[startup] Database check error ({type(e).__name__}): {e}")
        needs_migrate = True

    if needs_migrate:
        call_command("migrate", "--noinput")
        print("[startup] Migrations complete")

    UserModel = get_user_model()
    if not UserModel.objects.filter(is_superuser=True).exists():
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@georidge.local")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")
        UserModel.objects.create_superuser(email=email, password=password)
        print(f"[startup] Superuser created: {email}")
    else:
        print("[startup] Superuser exists, skipping creation")
