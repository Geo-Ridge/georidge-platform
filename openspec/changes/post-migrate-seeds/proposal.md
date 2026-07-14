## Why

Default data (themes, base maps, tenant) is seeded via 5 `RunPython` data migrations (0003, 0013, 0014, 0016, 0017). Three of these are patches on 0013. Data migrations are meant for transforming existing data, not seeding new data. This makes the migration files the "source of truth" for data, which is fragile and hard to maintain.

## What Changes

- Add `post_migrate` signal handlers in `accounts/apps.py` and `viewer/apps.py` to seed defaults automatically
- Each app seeds its own defaults (Tenant in accounts, ThemeProfile + BaseMap in viewer)
- Old data migrations left as-is (idempotent `get_or_create` calls are harmless)
- Seed data defined as Python constants next to the model definitions

## Capabilities

### New Capabilities
- `post-migrate-seeds`: Automatic default data seeding via `post_migrate` signals, replacing data migrations as the source of truth

### Modified Capabilities
(none)

## Impact

- `georidge_platform/apps/accounts/apps.py` — add `ready()` with `post_migrate` signal
- `georidge_platform/apps/viewer/apps.py` — add `ready()` with `post_migrate` signal
- Old data migrations (0003, 0013, 0014, 0016, 0017) remain unchanged — idempotent, harmless
