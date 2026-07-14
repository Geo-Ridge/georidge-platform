from django.db import migrations


def apply_changes(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")

    # Delete redundant Map Only theme (Minimal now uses map-only layout)
    ThemeProfile.objects.filter(name="Map Only").delete()

    # Fix GeoRidge Dark banner to match dark palette
    ThemeProfile.objects.filter(name="GeoRidge Dark").update(
        banner_bg="#1a1a2e",
    )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("viewer", "0016_fix_minimal_and_maponly_themes"),
    ]

    operations = [
        migrations.RunPython(apply_changes, reverse),
    ]
