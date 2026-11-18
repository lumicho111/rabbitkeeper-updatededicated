# Signed resource-051 update import

Upload **rabbit-float-build15-resource-051.zip** to this folder through the GitHub website (**Add file → Upload files → Commit changes**, on `main`).

The automated workflow `publish-resource-051-signed.yml` verifies the exact SHA-256, existing APK signing certificate, full resource manifest and individual file hashes, and then publishes the verified ZIP as the `resource-051` Release.

**Never upload private signing key files** (`float-release.p12`, `signing.properties`, or `float-android-signing-PRIVATE.zip`). Only the finished signed resource ZIP belongs here.
