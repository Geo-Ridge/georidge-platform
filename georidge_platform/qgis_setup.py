import os
import sys


def configure_pyqgis():
    if "QGIS_PREFIX_PATH" in os.environ:
        return

    candidates = [
        r"E:\OSGeo4W\apps\qgis-ltr",
    ]
    for prefix in candidates:
        python_dir = os.path.join(prefix, "python")
        bin_dir = os.path.join(prefix, "bin")
        plugins_dir = os.path.join(python_dir, "plugins")
        if os.path.isdir(python_dir) and os.path.isdir(bin_dir):
            if python_dir not in sys.path:
                sys.path.insert(0, python_dir)
            if plugins_dir not in sys.path:
                sys.path.insert(0, plugins_dir)
            os.environ.setdefault("QGIS_PREFIX_PATH", prefix.replace("\\", "/"))
            os.environ.setdefault(
                "GDAL_FILENAME_IS_UTF8", "YES"
            )
            os.environ.setdefault("VSI_CACHE", "TRUE")
            os.environ.setdefault("VSI_CACHE_SIZE", "1000000")
            cur_path = os.environ.get("PATH", "")
            if bin_dir not in cur_path:
                os.environ["PATH"] = bin_dir + os.pathsep + cur_path
            return True
    return False