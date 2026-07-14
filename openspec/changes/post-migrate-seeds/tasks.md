## 1. Accounts app seed

- [x] 1.1 Add `DEFAULT_TENANT` constant and `seed_accounts_defaults` function to `accounts/apps.py`
- [x] 1.2 Register `post_migrate` signal in `AccountsConfig.ready()`

## 2. Viewer app seeds

- [x] 2.1 Add `DEFAULT_THEMES` and `DEFAULT_BASE_MAPS` constants to `viewer/apps.py`
- [x] 2.2 Add `seed_viewer_defaults` function using `get_or_create`
- [x] 2.3 Register `post_migrate` signal in `ViewerConfig.ready()`
