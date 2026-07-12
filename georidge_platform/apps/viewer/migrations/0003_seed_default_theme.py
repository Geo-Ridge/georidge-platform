from django.db import migrations


def seed_default_theme(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")
    if not ThemeProfile.objects.filter(is_default=True).exists():
        ThemeProfile.objects.create(
            name="GeoRidge Default",
            description="Default light theme for the GeoRidge Platform.",
            is_default=True,
            primary_color="#0d6efd",
            secondary_color="#6c757d",
            background_color="#ffffff",
            surface_color="#f8f9fa",
            text_color="#212529",
            text_muted_color="#6c757d",
            border_color="#dee2e6",
            toolbar_bg="#f8f9fa",
            toolbar_border="#dee2e6",
            panel_bg="#ffffff",
            panel_border="#dee2e6",
            statusbar_bg="#f8f9fa",
            statusbar_border="#dee2e6",
            accent_color="#0d6efd",
            danger_color="#dc3545",
            success_color="#198754",
            warning_color="#ffc107",
            show_legend=True,
            show_toolbar=True,
            show_statusbar=True,
            layout_preset="full",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("viewer", "0002_themeprofile"),
    ]

    operations = [
        migrations.RunPython(seed_default_theme, migrations.RunPython.noop),
    ]
