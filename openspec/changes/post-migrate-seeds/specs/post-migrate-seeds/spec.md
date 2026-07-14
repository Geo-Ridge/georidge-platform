## ADDED Requirements

### Requirement: Default tenant seeded automatically
The accounts app SHALL seed a default tenant via `post_migrate` signal after accounts migrations run.

#### Scenario: Fresh install
- **WHEN** `manage.py migrate` runs on a database with no tenant data
- **THEN** a Tenant with slug "default" and name "Default" is created

#### Scenario: Existing database
- **WHEN** `manage.py migrate` runs on a database that already has the default tenant
- **THEN** no duplicate tenant is created (get_or_create)

### Requirement: Default themes seeded automatically
The viewer app SHALL seed default theme profiles via `post_migrate` signal after viewer migrations run.

#### Scenario: Fresh install
- **WHEN** `manage.py migrate` runs on a database with no theme data
- **THEN** 10 ThemeProfile records are created (MapGuide Classic, MapStore Modern, QWC2 Default, GeoRidge Dark, High Contrast, Forest, Minimal, Warm Sunset, Ocean)

#### Scenario: Existing database
- **WHEN** `manage.py migrate` runs on a database that already has themes
- **THEN** no duplicate themes are created (get_or_create by name)

### Requirement: Default base maps seeded automatically
The viewer app SHALL seed default base maps via `post_migrate` signal after viewer migrations run.

#### Scenario: Fresh install
- **WHEN** `manage.py migrate` runs on a database with no base map data
- **THEN** 3 BaseMap records are created (OpenStreetMap, Satellite Esri, Terrain Esri)

#### Scenario: Existing database
- **WHEN** `manage.py migrate` runs on a database that already has base maps
- **THEN** no duplicate base maps are created (get_or_create by name)

### Requirement: Seed data is editable in source
The seed data SHALL be defined as Python constants in the same file as the signal handler, not in migration files.

#### Scenario: Developer adds new default theme
- **WHEN** developer adds a new theme to the seed constants
- **THEN** the next `manage.py migrate` creates the new theme automatically
