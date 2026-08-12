package com.furoftheweak.device.control

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import android.view.accessibility.AccessibilityNodeInfo

/**
 * In-process bridge between ControlForegroundService (which owns the
 * WebRTC "input" DataChannel) and DeviceControlAccessibilityService (the
 * only component actually allowed to inject gestures) — they're different
 * Android components with no direct call path, so this singleton is how
 * one reaches the other.
 */
object InputInjector {

    private const val TAG = "InputInjector"
    private const val MIN_GESTURE_DURATION_MS = 16L

    @Volatile
    private var service: AccessibilityService? = null

    @Volatile
    var displayWidth: Int = 0

    @Volatile
    var displayHeight: Int = 0

    private var activePath: Path? = null
    private var pathStartTime: Long = 0L
    private val mainHandler = Handler(Looper.getMainLooper())

    fun attach(service: AccessibilityService) {
        this.service = service
    }

    fun detach(service: AccessibilityService) {
        if (this.service === service) this.service = null
    }

    val isAvailable: Boolean get() = service != null

    fun handlePointer(message: DeviceInputMessage) {
        val svc = service
        if (svc == null) {
            Log.w(TAG, "Pointer event dropped — accessibility service not enabled")
            return
        }
        if (displayWidth <= 0 || displayHeight <= 0) return
        val nx = message.x ?: return
        val ny = message.y ?: return
        val x = nx.coerceIn(0f, 1f) * displayWidth
        val y = ny.coerceIn(0f, 1f) * displayHeight

        when (message.action) {
            "down" -> {
                activePath = Path().apply { moveTo(x, y) }
                pathStartTime = SystemClock.uptimeMillis()
            }
            "move" -> activePath?.lineTo(x, y)
            "up" -> {
                val path = (activePath ?: Path().apply { moveTo(x, y) }).apply { lineTo(x, y) }
                dispatch(svc, path)
                activePath = null
            }
        }
    }

    private fun dispatch(service: AccessibilityService, path: Path) {
        val duration = (SystemClock.uptimeMillis() - pathStartTime).coerceAtLeast(MIN_GESTURE_DURATION_MS)
        val stroke = GestureDescription.StrokeDescription(path, 0, duration)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()
        mainHandler.post { service.dispatchGesture(gesture, null, null) }
    }

    /**
     * Best-effort only, by platform limitation: AccessibilityService has no
     * general raw-keycode injection API, so full KeyboardEvent passthrough
     * isn't achievable this way. This covers the one thing that actually
     * works — appending a single printable character to whichever field
     * currently has accessibility focus — not arbitrary key events. Stated
     * explicitly here and in docs/DEVICE_CONTROL_PROTOCOL.md rather than
     * pretending full keyboard support exists.
     */
    fun handleKey(message: DeviceInputMessage) {
        if (message.action != "down") return
        val svc = service ?: return
        val focused = svc.findFocus(AccessibilityNodeInfo.FOCUS_INPUT) ?: return
        if (!focused.isEditable) return
        val char = message.key?.takeIf { it.length == 1 } ?: return

        val newText = (focused.text?.toString().orEmpty()) + char
        val arguments = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, newText)
        }
        focused.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
    }
}
