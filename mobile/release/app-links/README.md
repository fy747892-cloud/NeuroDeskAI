# Production App Links

Publish these files on `https://app.neurodesk.ai` before enabling production App/Universal Links.

## Android

1. Replace `REPLACE_WITH_RELEASE_CERT_SHA256` in `assetlinks.json` with the SHA-256 fingerprint of the release signing certificate.
2. Upload the file to:

```text
https://app.neurodesk.ai/.well-known/assetlinks.json
```

3. Serve it with `Content-Type: application/json`.
4. Verify with:

```bash
adb shell pm verify-app-links --re-verify ai.neurodesk.mobile
adb shell pm get-app-links ai.neurodesk.mobile
```

## iOS

1. Replace `REPLACE_WITH_APPLE_TEAM_ID` in `apple-app-site-association` with the Apple Team ID.
2. Upload the file to:

```text
https://app.neurodesk.ai/.well-known/apple-app-site-association
```

3. Serve it without a `.json` extension and with `Content-Type: application/json`.
4. Keep `applinks:app.neurodesk.ai` enabled in the iOS App ID and provisioning profile.
