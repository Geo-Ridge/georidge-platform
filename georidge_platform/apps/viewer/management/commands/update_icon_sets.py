import os
import shutil

from django.core.management.base import BaseCommand

ICONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "static", "viewer", "icons"
)


class Command(BaseCommand):
    help = "Copy new icon files from the default icon set into all existing icon sets."

    def handle(self, *args, **options):
        default_dir = os.path.join(ICONS_DIR, "default")
        if not os.path.isdir(default_dir):
            self.stderr.write(self.style.ERROR(f"Default icon set not found: {default_dir}"))
            return

        default_files = set(os.listdir(default_dir))
        copied = 0

        for entry in sorted(os.listdir(ICONS_DIR)):
            set_dir = os.path.join(ICONS_DIR, entry)
            if not os.path.isdir(set_dir) or entry == "default":
                continue

            for filename in default_files:
                src = os.path.join(default_dir, filename)
                dst = os.path.join(set_dir, filename)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    self.stdout.write(f"  {entry}/{filename}")
                    copied += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Copied {copied} new icon file(s)."))
