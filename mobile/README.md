# NeuroDesk AI Mobile

Sprint 14 mobile MVP app. The app consumes the same backend API as the web app and keeps auth tokens in platform secure storage.

## Project root

Use this `mobile/` directory as the Flutter project root. The native platform folders (`android/`, `ios/`, `web/`, `windows/`, `macos/`, `linux/`) are aligned with the real MVP code in `lib/`.

`mobile/neurodeskai_mobile/` is the older generated Flutter template and is not the active app.

## Run

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

For Android emulator against a host backend, use:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Scope

- Login with `/api/v1/auth/login`
- Register with `/api/v1/auth/register`
- Refresh token retry with `/api/v1/auth/refresh`
- Secure token storage via `flutter_secure_storage`
- Remember-me login toggle
- Biometric unlock for saved sessions on supported devices
- Global API health banner and transient read retry
- Deep link route aliases for module/detail URLs
- Protected dashboard shell
- Dashboard summary
- Task list with complete action
- Appointment list
- Calls module with manual call transcript capture, TXT transcript import, and AI analysis trigger
- AI approval list with approve/reject actions and approval materialization through `tasks/from-approval`, `appointments/from-approval`, or `deals/from-approval`
- Manual conversation transcript capture
- AI analysis request from conversations
- Notifications center with read action
- Notification source navigation to deep-linked module routes
- AI Chat sessions and messages
- Contacts/CRM list, detail, memory and notes
- Semantic search
- Deals pipeline
- Priority queue
- Analytics overview
- Files list/analyze/delete and native file picker upload
- File upload pre-check for the backend 25 MB size limit
- Email accounts/messages/sync surface with native browser connect launch
- Email OAuth mobile callback return screen
- Settings profile/API/account screen

## Local smoke checklist

```bash
flutter analyze
flutter test
flutter build apk --debug --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Backend must answer `GET http://localhost:8000/health`, and Android emulator builds must use `http://10.0.2.2:8000`.

## Android release signing

Release builds read signing secrets from `mobile/android/key.properties` or environment variables. Keep the keystore and passwords out of git.

`mobile/android/key.properties` format:

```properties
storeFile=C:\\path\\to\\neurodesk-release.jks
storePassword=...
keyAlias=...
keyPassword=...
```

Equivalent environment variables:

```bash
ANDROID_KEYSTORE_PATH=C:\\path\\to\\neurodesk-release.jks
ANDROID_KEYSTORE_PASSWORD=...
ANDROID_KEY_ALIAS=...
ANDROID_KEY_PASSWORD=...
```

If release signing is not configured, local release builds fall back to debug signing so the build command remains usable during development.

## Deep link production setup

The app is wired for:

- Android custom scheme: `neurodesk://app/...`
- Android App Links: `https://app.neurodesk.ai/...`
- iOS custom scheme: `neurodesk://app/...`
- iOS Universal Links entitlement: `applinks:app.neurodesk.ai`

Before production, publish the Android `assetlinks.json` and iOS `apple-app-site-association` files on `app.neurodesk.ai`, then verify the Android SHA-256 certificate fingerprint and Apple Team/App ID values.

Templates are in `mobile/release/app-links/`.

## Platform readiness

- Android release builds include `INTERNET` for backend API access and `USE_BIOMETRIC` for saved-session unlock.
- iOS includes `NSFaceIDUsageDescription` for biometric unlock review compliance.
- iOS Associated Domains are configured through `Runner.entitlements`.

Current MVP excludes offline outbox/cache, push notifications/FCM, production domain publishing/verification for App/Universal Link association files, crash reporting, product analytics events, tablet/foldable polish, production release automation, and offline upload queueing for large files.
