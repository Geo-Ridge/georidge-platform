## Why

17 viewer migration files exist, but 5 are empty shells and the rest are incremental schema changes that should have been one migration. Django's `squashmigrations` already produced a single file (`0001_initial_squashed_0017_...py`) with 3 operations. This replaces all 17 originals.

## What Changes

- Delete 17 original viewer migration files
- Rename squashed file to `0001_initial.py`
- The squashed file has `replaces = [...]` so existing databases transition safely

## Capabilities

### New Capabilities
- `squash-viewer-migrations`: Replace 17 viewer migration files with a single squashed migration

### Modified Capabilities
(none)

## Impact

- `georidge_platform/apps/viewer/migrations/` — 17 files deleted, 1 renamed
- No schema changes, no data changes
- Safe for existing databases (replaces list handles transition)
