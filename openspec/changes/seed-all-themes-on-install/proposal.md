## Why

On a fresh platform install, only 1 theme ("GeoRidge Default") is created by migrations. The other 10 themes and 3 base maps require manually running DEBUG-only management commands (`seed_layout_themes`, `seed_test_themes`, `seed_base_maps`). New installs should ship with all themes and base maps available out of the box.

## What Changes

- Add a new data migration (`0013_seed_platform_defaults`) that seeds all 10 remaining themes and 3 base maps on `migrate`
- Delete the `seed_layout_themes`, `seed_test_themes`, and `seed_base_maps` management commands — the migration becomes the single source of truth
- The migration is idempotent (`get_or_create` by name) — safe for existing installs that already ran the seed commands

## Capabilities

### New Capabilities
- `platform-default-seeding`: Data migration that auto-seeds all themes and base maps on fresh install

### Modified Capabilities

## Impact

- **Migrations**: New `viewer/0013_seed_platform_defaults.py`
- **Deleted files**: `viewer/management/commands/seed_layout_themes.py`, `seed_test_themes.py`, `seed_base_maps.py`
- **Existing installs**: Safe — `get_or_create` skips already-existing records
- **Test/demo projects**: Not included in migration (no auto-seeding of projects)
