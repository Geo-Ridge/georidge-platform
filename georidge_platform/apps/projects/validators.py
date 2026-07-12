import os
import zipfile

from django.core.exceptions import ValidationError


def validate_qgz_or_zip(value):
    if not hasattr(value, "name") or not value.name:
        raise ValidationError("Only .qgz or .zip files are accepted.")
    ext = os.path.splitext(value.name)[1].lower()
    if ext == ".zip":
        try:
            zf = zipfile.ZipFile(value)
            qgz_files = [n for n in zf.namelist() if n.lower().endswith(".qgz")]
            if not qgz_files:
                raise ValidationError("ZIP file must contain at least one .qgz project file.")
            zf.close()
        except zipfile.BadZipFile:
            raise ValidationError("Invalid ZIP file.")
        value.seek(0)
    elif ext != ".qgz":
        raise ValidationError("Only .qgz or .zip files are accepted.")
    if value.size > 500 * 1024 * 1024:
        raise ValidationError("File size must be less than 500 MB.")
