from django.db import migrations


def set_qwc2_show_banner(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")
    ThemeProfile.objects.filter(name="QWC2 Default", layout_preset="qwc2").update(
        show_banner=True
    )


def unset_qwc2_show_banner(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")
    ThemeProfile.objects.filter(name="QWC2 Default", layout_preset="qwc2").update(
        show_banner=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ("viewer", "0002_alter_themeprofile_layout_preset"),
    ]

    operations = [
        migrations.RunPython(set_qwc2_show_banner, unset_qwc2_show_banner),
    ]
