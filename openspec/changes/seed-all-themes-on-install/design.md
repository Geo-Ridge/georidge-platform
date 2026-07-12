## Context

Fresh platform installs only get 1 theme ("GeoRidge Default") via migration `0003`. The other 10 themes and 3 base maps exist only in DEBUG-only management commands that must be run manually. This creates a gap: new installs are incomplete out of the box.

The existing `0003_seed_default_theme` migration established the pattern of seeding data via `RunPython`. We extend this pattern.

## Goals / Non-Goals

**Goals:**
- All 11 themes available on fresh install via `python manage.py migrate`
- All 3 base maps available on fresh install via `python manage.py migrate`
- Safe for existing installs (idempotent, no duplicates)
- Single source of truth for theme/base map definitions

**Non-Goals:**
- Auto-seeding test/demo projects
- Changing the ThemeProfile or BaseMap models
- Modifying the existing `0003_seed_default_theme` migration

## Decisions

**1. New migration `0013_seed_platform_defaults` instead of modifying `0003`**

`0003` has already run on all existing installs. Modifying it would require a squashed migration or risk double-seeding. A new migration is safe and follows Django conventions.

**2. `get_or_create` by name for idempotency**

Each theme and base map is looked up by `name` before creation. If it already exists (from manual seed commands or a previous run), it's skipped. No duplicates, no errors.

**3. Delete management commands**

`seed_layout_themes`, `seed_test_themes`, and `seed_base_maps` become redundant. The migration is the single source of truth. Keeping dead commands creates confusion about which is canonical.

**4. Theme data consolidated in the migration file**

All 10 theme definitions live in `0013_seed_platform_defaults.py`. No shared constants file needed — the migration is self-contained.

## Risks / Trade-offs

- **Migration contains data** → Acceptable for seed data. These are platform defaults, not user data. The pattern is already established by `0003`.
- **Future theme additions require a new migration** → Correct. This is intentional — theme changes should be tracked in version control like any schema change.
- **Deleting commands breaks `flush` workflow** → After `flush`, themes are gone and only reappear on next `migrate`. Acceptable — `migrate` is the canonical seed path now.
