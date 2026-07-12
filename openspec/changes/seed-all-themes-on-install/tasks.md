## 1. Create data migration

- [x] 1.1 Create `viewer/migrations/0013_seed_platform_defaults.py` with theme and base map definitions
- [x] 1.2 Implement `seed_platform_defaults` function using `get_or_create` for all 10 themes (excluding GeoRidge Default from 0003)
- [x] 1.3 Implement base map seeding for OpenStreetMap, Satellite (Esri), Terrain (Esri)
- [x] 1.4 Add reverse operation (noop) to the migration

## 2. Delete management commands

- [x] 2.1 Delete `viewer/management/commands/seed_layout_themes.py`
- [x] 2.2 Delete `viewer/management/commands/seed_test_themes.py`
- [x] 2.3 Delete `viewer/management/commands/seed_base_maps.py`

## 3. Verify

- [x] 3.1 Run `python manage.py migrate` on fresh database and verify 11 themes + 3 base maps exist
- [x] 3.2 Run `python manage.py migrate` on database with existing themes and verify no duplicates
