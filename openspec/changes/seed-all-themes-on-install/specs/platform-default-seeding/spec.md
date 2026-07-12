## ADDED Requirements

### Requirement: All themes seeded on fresh install
The system SHALL create all 11 platform themes when `python manage.py migrate` runs on a fresh database. The themes are: GeoRidge Default (already in 0003), MapGuide Classic, MapStore Modern, QWC2 Default, GeoRidge Dark, High Contrast, Forest, Minimal, Map Only, Warm Sunset, and Ocean.

#### Scenario: Fresh install gets all themes
- **WHEN** `python manage.py migrate` runs on a database with no ThemeProfile records
- **THEN** 11 ThemeProfile records exist after migration completes

#### Scenario: Existing install with themes already present
- **WHEN** `python manage.py migrate` runs on a database that already has ThemeProfile records (e.g. from previous manual seed commands)
- **THEN** no duplicate ThemeProfile records are created and existing records are unchanged

### Requirement: All base maps seeded on fresh install
The system SHALL create all 3 platform base maps (OpenStreetMap, Satellite Esri, Terrain Esri) when `python manage.py migrate` runs on a fresh database.

#### Scenario: Fresh install gets all base maps
- **WHEN** `python manage.py migrate` runs on a database with no BaseMap records
- **THEN** 3 BaseMap records exist after migration completes

#### Scenario: Existing install with base maps already present
- **WHEN** `python manage.py migrate` runs on a database that already has BaseMap records
- **THEN** no duplicate BaseMap records are created and existing records are unchanged

### Requirement: Seed commands removed
The management commands `seed_layout_themes`, `seed_test_themes`, and `seed_base_maps` SHALL be deleted. The migration `0013_seed_platform_defaults` is the single source of truth for platform default data.

#### Scenario: Deleted commands no longer exist
- **WHEN** a user runs `python manage.py seed_layout_themes` (or `seed_test_themes` or `seed_base_maps`)
- **THEN** the command is not found (Unknown command error)
