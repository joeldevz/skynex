# Refactor: Split UserService into 3 modules

## Before
- src/services/user.service.ts (800 lines, handles auth + profile + preferences)

## After
- src/services/auth.service.ts (handles login, logout, token refresh)
- src/services/profile.service.ts (handles CRUD on user profiles)
- src/services/preferences.service.ts (handles user settings)

## Changes
- All 47 tests updated to import from new modules
- 3 new interfaces created (IAuthService, IProfileService, IPreferencesService)
- Old user.service.ts deleted
