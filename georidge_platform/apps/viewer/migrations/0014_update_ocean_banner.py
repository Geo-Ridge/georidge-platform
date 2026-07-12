from django.db import migrations


def update_ocean_banner(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")
    ThemeProfile.objects.filter(name="Ocean").update(banner_bg="#0077b6")


def reverse(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")
    ThemeProfile.objects.filter(name="Ocean").update(banner_bg="#03045e")


class Migration(migrations.Migration):

    dependencies = [
        ("viewer", "0013_seed_platform_defaults"),
    ]

    operations = [
        migrations.RunPython(update_ocean_banner, reverse),
    ]
