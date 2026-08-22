# Devices module: pairing & signaling protocol

Remote screen viewing/control of a user's own Android device (AirDroid-style), gated behind `ENABLE_DEVICE_CONTROL` (default off). This document is the contract between the backend (built) and the Android client (**not yet built** — see [Android client requirements](#android-client-requirements-not-yet-built)). It's the reference for building that client later without having to re-derive the wire format from the backend source.

No API key or Android SDK is required to read or test everything on the backend/web side of this contract — the backend has no dependency on the Android app existing.

## Overview

```text
Web session (authenticated)          Android device (paired)
        │                                     │
        │  POST /devices/pairing-codes        │
        │  → { code, qr_code_data_url }       │
        │                                     │
        │           code shown/scanned  ────► │
        │                                     │  POST /devices/pairing-codes/{code}/exchange
        │                                     │  → { device, device_secret }  (shown once)
        │                                     │
        │  POST /devices/{id}/sessions        │
        │  → { session_id, web_ticket, ... }  │
        │                                     │  GET /devices/{id}/sessions/pending  (polled)
        │                                     │  (Authorization: Bearer <device_secret>)
        │                                     │  → { session_id }
        │                                     │
        │                                     │  POST /devices/{id}/sessions/token
        │                                     │  (Authorization: Bearer <device_secret>)
        │                                     │  → { ticket, ice_servers }
        │                                     │
        │  WS  /devices/sessions/{id}/signal?ticket=...        (both peers)
        │  ◄────────────  SDP offer/answer + ICE candidates  ────────────►
        │                                     │
        │  ◄═══════════════ WebRTC media + "input" data channel ═══════════════►
        │              (peer-to-peer or via TURN — never through the backend)
```

## Pairing

1. **Web session generates a code.** `POST /api/v1/devices/pairing-codes` (authenticated, rate-limited 5/5min). Response: `{ code, expires_at, qr_code_data_url }`. `code` is shown once — the server stores only its hash. TTL is `DEVICE_PAIRING_CODE_TTL_SECONDS` (default 300s).
2. **Device exchanges the code.** `POST /api/v1/devices/pairing-codes/{code}/exchange` (no user auth — the code itself is the credential; rate-limited 10/5min per IP). Body:
   ```json
   { "code": "...", "device_name": "Pixel 8", "device_fingerprint": "<stable per-install id>", "platform": "android" }
   ```
   Response: `{ "device": {...}, "device_secret": "..." }`. `device_secret` is shown **once** — persist it on-device (e.g. Android Keystore-backed storage); the server stores only its hash. This is the device's long-lived credential, independent of the pairing code.

This two-step, two-sided flow is the actual security property: generating a code proves control of the account, entering/scanning it on the phone proves physical possession. Neither step alone can register a device.

## Starting a session

1. **Controller (web) starts a session.** `POST /api/v1/devices/{device_id}/sessions` (authenticated). Response:
   ```json
   { "session_id": "...", "web_ticket": "...", "ice_servers": [...], "expires_at": "..." }
   ```
   `web_ticket` is a short-lived (`DEVICE_WS_TICKET_TTL_SECONDS`, default 60s) signaling credential scoped to exactly this session and the `controller` role.
2. **Target (device) discovers the session.** The device has no push channel — it doesn't otherwise know a session was started. `GET /api/v1/devices/{device_id}/sessions/pending`, header `Authorization: Bearer <device_secret>` (rate-limited 30/60s). Response: `{ "session_id": "..." | null }` — the newest unexpired `PENDING` session for this device, or `null` if none. Meant to be polled periodically (e.g. every few seconds) while the device app has sharing enabled.
3. **Target (device) requests its own ticket for the same session.** `POST /api/v1/devices/{device_id}/sessions/token`, header `Authorization: Bearer <device_secret>`, body `{ "session_id": "..." }`. Response: `{ "ticket": "...", "ice_servers": [...], "expires_in": 60 }`, ticket scoped to the `target` role.

A session only exists because the controller side created it first — a device can't unilaterally start a control session against itself.

## Signaling

`WS /api/v1/devices/sessions/{session_id}/signal?ticket=<web_ticket-or-device-ticket>`

Both peers connect to the same URL pattern (their own ticket, same `session_id`). Behind the scenes the backend relays messages by role — a peer never receives an echo of what it sent. Messages are JSON, one per WS frame:

```ts
type SignalMessage =
  | { type: "offer";  data: RTCSessionDescriptionInit }
  | { type: "answer"; data: RTCSessionDescriptionInit }
  | { type: "ice-candidate"; data: RTCIceCandidateInit }
  | { type: "peer-joined"; data: { role: "controller" | "target" } }  // relay-generated
  | { type: "peer-left";   data: { role: "controller" | "target" } }  // relay-generated
  | { type: "bye"; data: { reason?: string } }
```

Convention: the **target (Android device)** is the offering side, since it owns the media (screen capture) and creates the `input` data channel. The **controller (web)** answers and receives the data channel via `ondatachannel`.

`peer-joined` / `peer-left` are raised by the relay itself, not by a peer: they fire when the other side opens or closes its signaling socket. The controller needs them to tell "the phone has not joined yet" apart from "the phone joined and negotiation is under way" — without that distinction the browser can only show an indefinite spinner, with no idea whether anything is wrong. A client must ignore message types it does not recognise.

**Delivery is buffered, not fire-and-forget.** The two peers join seconds apart by design — the phone only discovers the session on its next poll, and its owner then has to accept the `MediaProjection` consent dialog. Anything published while the recipient is not yet subscribed is queued in a short-lived per-recipient Redis list (`MAILBOX_TTL_SECONDS`, 5 min) and replayed, in order, the moment that peer subscribes. Plain pub/sub dropped it, which reliably lost the target's SDP offer and its first ICE candidates. Both consequences follow from this and matter to a client implementation:

- A peer can receive an offer and its ICE candidates in one burst on connect, so candidates may arrive **before** the remote description is set. Queue them until it is (the web client does this in `IceCandidateQueue`); `addIceCandidate` throws otherwise.
- The mailbox is dropped when the session ends, so nothing from a finished session can leak into a later one.

- Session status flips `PENDING` → `ACTIVE` when the **target** connects — not on the first peer of either kind. `PENDING` is exactly the set `/sessions/pending` searches, and the controller opens its socket milliseconds after creating the session, well before the phone's next poll; flipping on the controller's connect made every session invisible to the device it was for.
- Starting a session supersedes any `PENDING`/`ACTIVE` session already open for that device (`ended_reason: "superseded"`), so a reloaded browser tab cannot leave an orphan for the phone to pick up.
- `/sessions/pending` only returns a session created within `DEVICE_SESSION_PENDING_TTL_SECONDS` (default 180s), so a phone never burns its consent dialog on a session nobody is listening to. Every poll also refreshes the device's `last_seen_at`, which is what drives the web UI's online indicator.
- A `bye` (sent explicitly, or implied by either side disconnecting, or by revoking the device from the web UI) ends the session and closes both sockets.
- Sessions hard-expire after `DEVICE_SESSION_MAX_DURATION_SECONDS` (default 3600s) regardless of activity; a periodic worker sweep (`app/services/device_service.py::sweep_stale_devices`) cleans up anything left `PENDING`/`ACTIVE` past its `expires_at`.
- The backend never inspects or stores message contents beyond relaying them — no recording, by construction (media itself never transits this process at all).

## Input data channel

Once connected, the target (device) creates an `RTCDataChannel("input")`. The controller (web) sends normalized events on it:

```ts
type DeviceInputMessage =
  | { type: "pointer"; action: "down" | "move" | "up"; x: number; y: number } // x, y ∈ [0, 1], relative to the video frame
  | { type: "key"; action: "down" | "up"; key: string; code: string }         // KeyboardEvent.key / .code
```

The three navigation keys are sent as `key` messages with `key` set to `"BACK"`, `"HOME"`, or `"RECENTS"`; the device maps those onto `AccessibilityService.performGlobalAction`, which is the supported way to press them. Any other `key` value falls under the partial text-insertion support described below.

Normalized `x`/`y` keep the message independent of either peer's actual resolution — the device maps them back to real screen pixels.

## Android client

Lives in `android/` (Kotlin/Gradle, not buildable/testable from the environment that wrote it — see its own notes). Implements this contract in full:

- **`MediaProjection`** for screen capture. This forces Android's own "this app is capturing your screen" system dialog — non-bypassable, and exactly the explicit-consent flow this project already requires for any sensitive capability (see `Proje.md`'s camera/mic/screen rules). `HomeActivity` requests consent and hands the raw result `Intent` to `ControlForegroundService`, which builds a `ScreenCapturerAndroid` from it directly rather than resolving a `MediaProjection` object itself.
- **`AccessibilityService`** (`DeviceControlAccessibilityService`) for input injection, requiring a separate, explicit grant in Android Settings (not requestable via a normal runtime permission dialog) — `HomeActivity` detects this and prompts before allowing sharing to start. Pointer events dispatch via `GestureDescription`, and the Back/Home/Recents keys via `performGlobalAction`. Everything else on the keyboard is honest best-effort only — no general raw-keycode injection API exists on `AccessibilityService`, so only single-character insertion into the currently-focused editable field is supported, not arbitrary `KeyboardEvent` passthrough (see `InputInjector.kt`).
- **A persistent foreground-service notification** (`ControlForegroundService`, `foregroundServiceType="mediaProjection"`) for the entire duration of an active control session. Android 14+ enforces this regardless; treated as a hard requirement here too.
- **Session discovery**: the device has no push channel, so `HomeActivity` polls `GET /{device_id}/sessions/pending` every ~3s while the user has sharing toggled on **and the app is in the foreground** — deliberately not an always-on background service, matching this project's explicit-consent posture (the owner opens the app to actively allow a session, rather than the phone silently listening at all times). An always-listening mode (push notification, persistent background service) is a natural v2, not implemented here.
- The pairing REST contract and signaling/data-channel wire format above, unchanged. Pairing uses manual 8-character code entry (`PairingActivity`), not camera/QR scanning, for v1.

**Honest limitations:** the backend has no way to verify the Android app actually shows the mandated foreground notification — it only knows a session is `ACTIVE`. Keyboard input support is partial (see above). Both are called out explicitly rather than implied, the same way `docs/SECURITY.md` documents its own residual risks instead of glossing over them.

## Security summary

See `docs/SECURITY.md` for the full table. Specific to this module: mutual pairing confirmation (§Pairing), IDOR-safe ownership checks on every device/session lookup, full audit logging (`DEVICE_*` actions in `app/core/audit_actions.py`) including failed pairing attempts, rate limiting on both pairing endpoints, time-limited + actively-revocable sessions, and `ENABLE_DEVICE_CONTROL` defaulting off as the module's overall blast-radius control.
