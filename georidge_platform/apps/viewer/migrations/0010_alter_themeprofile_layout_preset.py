from django.db import migrations, models


def migrate_full_to_mapguide(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")
    ThemeProfile.objects.filter(layout_preset="full").update(layout_preset="mapguide")


def reverse_migrate(apps, schema_editor):
    ThemeProfile = apps.get_model("viewer", "ThemeProfile")
    ThemeProfile.objects.filter(layout_preset="mapguide").update(layout_preset="full")


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0009_layersearchconfig_available_fields_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='themeprofile',
            name='layout_preset',
            field=models.CharField(choices=[('mapguide', 'MapGuide'), ('mapstore', 'MapStore'), ('qwc2', 'QWC2'), ('map-only', 'Map Only')], default='mapguide', max_length=20),
        ),
        migrations.RunPython(migrate_full_to_mapguide, reverse_migrate),
    ]
