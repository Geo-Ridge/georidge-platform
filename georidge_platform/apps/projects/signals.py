import logging
import os
import shutil

from django.conf import settings
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Project

logger = logging.getLogger(__name__)


@receiver(post_delete, sender="projects.Project")
def delete_project_files(sender, instance, **kwargs):
    """Remove the project's media directory when its DB row is deleted.

    Django does not delete FileField contents automatically, so deleting a
    project via the admin UI (including bulk delete) used to orphan the .qgz,
    the extracted GeoPackage, and any project media on disk. This removes the
    whole ``MEDIA_ROOT/projects/<pk>/`` directory, covering both the project
    file and everything extracted alongside it.
    """
    if not instance.pk:
        return

    # Derive the storage directory from the actual file path when available
    # (e.g. projects/5), falling back to the pk-based convention. The whole
    # directory is removed because zip uploads extract the GeoPackage and
    # media alongside the .qgz under the same project directory.
    if instance.file and instance.file.name:
        rel_dir = os.path.dirname(instance.file.name)
    else:
        rel_dir = os.path.join("projects", str(instance.pk))
    project_dir = os.path.normpath(os.path.join(settings.MEDIA_ROOT, rel_dir))
    media_root = os.path.normpath(settings.MEDIA_ROOT)
    # Guard against deleting MEDIA_ROOT itself (e.g. when instance.file.name is
    # empty) or anything outside it, including sibling paths like /mediaevil.
    if project_dir == media_root or not project_dir.startswith(media_root + os.sep):
        logger.warning("Refusing to remove path outside MEDIA_ROOT: %s", project_dir)
        return
    try:
        if os.path.isdir(project_dir):
            shutil.rmtree(project_dir)
            logger.info("Removed project media directory: %s", project_dir)
    except OSError as e:
        logger.warning("Could not remove project media directory %s: %s", project_dir, e)


@receiver(pre_save, sender=Project)
def track_file_change(sender, instance, **kwargs):
    """Record on the instance whether its project file is changing.

    The post_save receiver uses this to sync LayerSearchConfig rows from QGIS
    Server only when the .qgz actually changed (upload, re-upload, replace).
    Syncing on every save would clobber manual search-config edits made in the
    admin (sync_search_layers re-activates and re-fields configs).

    Django's pre_save signal fires before FileField writes the upload to
    storage, so ``instance.file.name`` is still the raw value: either a freshly
    attached upload name, or the stored path when loaded from the DB. Comparing
    it to the stored DB value reliably detects "new file attached".
    """
    if not instance.pk:
        # Brand-new row: sync once after save if a file was attached.
        instance._project_file_changed = bool(instance.file and instance.file.name)
        return
    try:
        old_name = Project.objects.only("file").get(pk=instance.pk).file.name
    except Project.DoesNotExist:
        instance._project_file_changed = bool(instance.file and instance.file.name)
        return
    instance._project_file_changed = bool(instance.file and instance.file.name) and old_name != instance.file.name


@receiver(post_save, sender=Project)
def sync_search_layers_on_file_change(sender, instance, created, **kwargs):
    """Auto-create/update search layer configs when the project file changes.

    Previously configs only appeared after manually running the admin action
    "Sync search layers from QGIS Server". This makes the sync automatic on
    upload/re-upload while leaving configs untouched for unrelated edits.
    """
    file_changed = getattr(instance, "_project_file_changed", False)
    if not file_changed:
        return
    try:
        from georidge_platform.apps.viewer.services import sync_search_layers

        sync_search_layers(instance)
        logger.info("Auto-synced search layers for project %s after file change", instance.pk)
    except Exception:
        logger.exception("Auto-sync of search layers failed for project %s", instance.pk)
