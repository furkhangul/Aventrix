# FurOfTheWeak Device (Android client)

Implements the Android side of the Devices module's pairing/control protocol
(`docs/DEVICE_CONTROL_PROTOCOL.md`) — screen viewing + remote input control
for the web dashboard's `/devices` page.

**Verified (2026-08-10):** `./gradlew :app:assembleDebug` builds clean end to
end (Gradle 9.3.0, AGP 8.7.2, JDK from Android Studio's bundled JBR) and
produces `app/build/outputs/apk/debug/app-debug.apk`. One real bug was found
and fixed in the process — see below. This has not yet been run on a device.

## Build

1. Open the `android/` folder directly in Android Studio (not the repo root) — "Open" → select this folder. The Gradle wrapper is checked in, so it'll sync without prompting to create one.
2. Or from the command line: `./gradlew :app:assembleDebug` (needs `JAVA_HOME` pointed at a JDK 17+; Android Studio's bundled JBR at `Android Studio/jbr` works).
3. Run on a physical device (the emulator's screen capture / AccessibilityService support is unreliable for this kind of app — a real phone over USB is the realistic path).

## Fixed since first draft

- `net/ApiClient.kt` imported `retrofit2.converter.kotlinx.serialization.asConverterFactory`, but that extension actually lives in `com.jakewharton.retrofit2.converter.kotlinx.serialization` (the `com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter` artifact keeps its own package prefix, not `retrofit2.*`). Fixed the import; this was the only compile error.

## Previously flagged as risky, now confirmed fine by the compiler

- `ScreenCapturerAndroid(projectionData, callback)` in `control/ControlForegroundService.kt`, constructed directly from the raw `MediaProjection` consent `Intent` — compiles as written against `io.getstream:stream-webrtc-android:1.3.5`.
- `PeerConnectionFactory.createVideoSource(isScreencast: Boolean)` — correct overload for the pinned WebRTC version.

## Known limitations (by design, not bugs)

- **No background listening.** Session polling (`GET /sessions/pending`) only runs while `HomeActivity` is open and "Ekran paylaşımını aç" is on — not an always-on background service. Matches this project's explicit-consent posture elsewhere; a push/background mode is a reasonable v2, not built here.
- **Partial keyboard support.** `AccessibilityService` has no general raw-keycode injection API. Only single-character insertion into the currently-focused editable field works (`InputInjector.handleKey`) — not full `KeyboardEvent` passthrough. Pointer/touch (tap, drag) works fully via `dispatchGesture`.
- **Manual pairing code only.** No camera/QR scanning in v1 — enter the 8-character, case-sensitive code shown on the web `/devices` page by hand.
