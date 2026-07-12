from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("publishing", "0002_change_related_name_for_project_clash"),
        ("projects", "0004_migrate_published_data_to_project"),
    ]

    operations = [
        migrations.DeleteModel(
            name="PublishedProject",
        ),
    ]
