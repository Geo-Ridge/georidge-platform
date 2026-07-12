from django.conf import settings
from django.core.management.base import BaseCommand
from georidge_platform.apps.accounts.models import Tenant, User
from georidge_platform.apps.projects.models import Project
from georidge_platform.apps.viewer.models import ThemeProfile
from georidge_platform.apps.datasources.models import ConnectionProfile


class Command(BaseCommand):
    help = "Create default tenant and assign existing records to it"

    def handle(self, *args, **options):
        slug = settings.DEFAULT_TENANT_SLUG
        tenant, created = Tenant.objects.get_or_create(
            slug=slug,
            defaults={"name": slug.capitalize()},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created tenant '{slug}'"))
        else:
            self.stdout.write(f"Tenant '{slug}' already exists")

        for user in User.objects.filter(tenant__isnull=True):
            user.tenant = tenant
            user.save(update_fields=["tenant"])
            self.stdout.write(f"  Assigned user '{user.email}' to tenant '{slug}'")

        for project in Project.objects.filter(tenant__isnull=True):
            project.tenant = tenant
            project.save(update_fields=["tenant"])
            self.stdout.write(f"  Assigned project '{project.name}' to tenant '{slug}'")

        for profile in ThemeProfile.objects.filter(tenant__isnull=True):
            profile.tenant = tenant
            profile.save(update_fields=["tenant"])
            self.stdout.write(f"  Assigned theme profile '{profile.name}' to tenant '{slug}'")

        for profile in ConnectionProfile.objects.filter(tenant__isnull=True):
            profile.tenant = tenant
            profile.save(update_fields=["tenant"])
            self.stdout.write(f"  Assigned connection profile '{profile.name}' to tenant '{slug}'")

        self.stdout.write(self.style.SUCCESS("Seed complete"))
