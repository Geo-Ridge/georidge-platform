## Context

Viewer app has 5 data migrations with `RunPython` operations that seed or patch theme/basemap data. These are now redundant because `post_migrate` signals in `apps.py` handle all seeding. The migrations still run but their `get_or_create` calls are idempotent — no harm, but unnecessary code.

## Goals / Non-Goals

**Goals:**
- Remove `RunPython` operations from 5 data migration files
- Keep migration files as empty shells (Django requires them for dependency tracking)
- Keep schema-only migrations untouched

**Non-Goals:**
- Deleting migration files entirely (Django will error if applied migration files are missing)
- Squashing migrations (can do later, not part of this change)
- Touching `0004_migrate_published_data_to_project.py` (real one-time data transform)

## Decisions

### 1. Empty shells, not deletion

Django tracks applied migrations in `django_migrations` table. If a file is missing that's been applied, Django raises `MigrationNotFoundError`. Keeping empty files avoids this.

### 2. Keep dependencies intact

Each migration's `dependencies` list stays unchanged. This ensures the migration graph remains valid for any database state.

## Risks / Trade-offs

- **Empty files are noise** → Acceptable. They're small and clearly labeled as legacy. Can be squashed later.
- **Old databases still have them applied** → No impact. Empty operations are truly no-ops.
