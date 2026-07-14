from django.apps import AppConfig


DEFAULT_TENANT = {"slug": "default", "name": "Default"}


def seed_accounts_defaults(apps, **kwargs):
    Tenant = apps.get_model("accounts", "Tenant")
    Tenant.objects.get_or_create(
        slug=DEFAULT_TENANT["slug"],
        defaults={"name": DEFAULT_TENANT["name"]},
    )


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "georidge_platform.apps.accounts"
    label = "accounts"

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(seed_accounts_defaults, sender=self)
