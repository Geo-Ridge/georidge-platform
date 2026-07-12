from django.db import migrations


def copy_published_data(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    PublishedProject = apps.get_model("publishing", "PublishedProject")
    for pub in PublishedProject.objects.select_related("project").iterator():
        project = pub.project
        project.published_by = pub.published_by
        project.published_at = pub.published_at
        project.published_version = pub.version_snapshot
        project.save(update_fields=["published_by", "published_at", "published_version"])


def reverse_copy(apps, schema_editor):
    PublishedProject = apps.get_model("publishing", "PublishedProject")
    for pub in PublishedProject.objects.select_related("project").iterator():
        project = pub.project
        project.published_by = None
        project.published_at = None
        project.published_version = None
        project.save(update_fields=["published_by", "published_at", "published_version"])


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_change_related_name_for_project_clash"),
        ("publishing", "0002_change_related_name_for_project_clash"),
    ]

    operations = [
        migrations.RunPython(copy_published_data, reverse_copy),
    ]
