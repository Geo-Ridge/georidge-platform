## 1. Startup Module

- [ ] 1.1 Create `georidge_platform/startup.py` with `run_startup()` that auto-migrates and creates default superuser
- [ ] 1.2 Wire `startup.run_startup()` into `georidge_platform/wsgi.py`

## 2. Fix Defaults and Remove Dead Code

- [ ] 2.1 Change default `DJANGO_SETTINGS_MODULE` in `wsgi.py` from `prod` to `dev`
- [ ] 2.2 Remove `configure_pyqgis()` import and call from `wsgi.py`
- [ ] 2.3 Remove `configure_pyqgis()` import and call from `manage.py`

## 3. Dockerfile and Env Files

- [ ] 3.1 Remove `RUN python manage.py migrate --noinput` from `Dockerfile`
- [ ] 3.2 Add `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` to `.env.linux.example`
- [ ] 3.3 Add `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` to `.env.win.example`
