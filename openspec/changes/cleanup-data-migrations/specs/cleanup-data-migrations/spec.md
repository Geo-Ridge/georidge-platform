## ADDED Requirements

### Requirement: Data migrations are empty shells
All viewer data migrations that seed or patch theme/basemap data SHALL have empty `operations = []`.

#### Scenario: Migration file exists
- **WHEN** a developer looks at migration files in `viewer/migrations/`
- **THEN** data migration files exist with valid `Migration` classes but empty `operations` lists

#### Scenario: Migrate runs cleanly
- **WHEN** `manage.py migrate` runs on any database state
- **THEN** no errors occur and all migrations are marked as applied

### Requirement: Schema migrations untouched
Schema-only migrations SHALL NOT be modified.

#### Scenario: Schema migration preserved
- **WHEN** a migration only contains `AddField`, `RemoveField`, `AlterField`, etc.
- **THEN** that migration is left completely unchanged
