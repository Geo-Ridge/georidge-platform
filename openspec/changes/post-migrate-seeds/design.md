## Context

Default data is currently seeded via 5 `RunPython` data migrations in the viewer app (0003, 0013, 0014, 0016, 0017). Three of these are patches on 0013. The seed data includes 10 themes, 3 base maps, and 1 default tenant. The `viewer` app also seeds a Tenant (which belongs to the `accounts` domain).

## Goals / Non-Goals

**Goals:**
- Move seed data from migrations to `post_migrate` signal handlers
- Each app seeds its own defaults (accounts → Tenant, viewer → ThemeProfile + BaseMap)
- Source code is the single source of truth for default data
- Old data migrations left as-is (idempotent, harmless)

**Non-Goals:**
- Deleting or squashing old migrations (risk-free cleanup for later)
- Adding seed data for other apps (audit, projects, etc.)
- Environment-specific overrides (future concern)

## Decisions

### 1. Each app seeds its own defaults

`accounts/apps.py` seeds Tenant. `viewer/apps.py` seeds ThemeProfile + BaseMap. This keeps concerns aligned — each app owns its data.

**Alternatives considered:**
- Single bootstrap app — overkill for this project size
- Single app seeds everything — crosses domain boundaries

### 2. post_migrate signal over management command

`post_migrate` fires automatically after `manage.py migrate`. No manual step required. This is Django's standard pattern (auth groups use it).

**Alternatives considered:**
- Management command — explicit but requires manual `loaddata` or `seed` step
- Fixtures — JSON files, no idempotency, manual step

### 3. Leave old migrations unchanged

Old `get_or_create` calls are idempotent. Both old migrations and new signals produce the same result. No migration squashing needed.

### 4. Seed data as module-level constants

Theme and basemap data defined as Python dicts in the same file as the signal handler. Easy to edit, version control, and override per-environment if needed later.

## Risks / Trade-offs

- **Signal runs on every migrate** → Mitigated by `get_or_create` (idempotent, no duplicates)
- **Tenant must exist before viewer seeds** → Not a problem: `ThemeProfile.tenant` is nullable, seeds work without Tenant. Accounts migrations run before viewer (dependency order).
- **Old migrations still run** → Harmless duplication. Both sources produce identical results.
