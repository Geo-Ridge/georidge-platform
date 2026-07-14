## ADDED Requirements

### Requirement: Squashed migration replaces all 17 originals
The viewer app shall have a single migration file `0001_initial.py` that replaces migrations 0001 through 0017.

#### Scenario: New database install
- **WHEN** a new database is created
- **THEN** only the squashed migration runs (3 CreateModel operations)

#### Scenario: Existing database with all 17 applied
- **WHEN** `migrate` runs on a database that already has 0001-0017
- **THEN** Django sees the `replaces` list and marks them all as applied
- **AND** no schema changes occur

## REMOVED Requirements

### Requirement: Original 17 viewer migration files exist
The 17 original migration files under `viewer/migrations/` are no longer needed.
