## Why

Five data migrations exist for theme seeding and patching (0003, 0013, 0014, 0016, 0017). Now that `post_migrate` signals in `apps.py` handle seeding, these are redundant. They still run on every `migrate` but do nothing useful. Clean them up to empty shells — the files must exist (Django tracks them) but the operations should be empty.

## What Changes

- Replace `RunPython` operations with empty `operations = []` in 5 viewer data migrations
- Keep the migration files and their `Migration` classes (Django requires them for dependency tracking)
- `0004_migrate_published_data_to_project.py` stays as-is (real one-time data transform, not seeding)

## Capabilities

### New Capabilities
- `cleanup-data-migrations`: Remove redundant RunPython operations from data migrations that are now handled by `post_migrate` signals

### Modified Capabilities
(none)

## Impact

- `georidge_platform/apps/viewer/migrations/0003_seed_default_theme.py` — empty operations
- `georidge_platform/apps/viewer/migrations/0010_alter_themeprofile_layout_preset.py` — remove RunPython, keep schema
- `georidge_platform/apps/viewer/migrations/0013_seed_platform_defaults.py` — empty operations
- `georidge_platform/apps/viewer/migrations/0014_update_ocean_banner.py` — empty operations
- `georidge_platform/apps/viewer/migrations/0016_fix_minimal_and_maponly_themes.py` — empty operations
- `georidge_platform/apps/viewer/migrations/0017_remove_maponly_fix_dark_banner.py` — empty operations
