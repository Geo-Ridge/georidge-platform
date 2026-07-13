from django.db import migrations


def fix_themes(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")

    ThemeProfile.objects.filter(name="Minimal").update(
        layout_preset="map-only",
        description="Bare map with search bar and base map switcher only.",
    )

    ThemeProfile.objects.filter(name="Map Only").delete()

    ThemeProfile.objects.filter(name="GeoRidge Dark").update(
        banner_bg="#1a1a2e",
    )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("viewer", "0015_add_popup_fields_to_layersearchconfig"),
    ]

    operations = [
        migrations.RunPython(fix_themes, reverse),
    ]
