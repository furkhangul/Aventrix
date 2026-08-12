package com.furoftheweak.device.accessibility

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import com.furoftheweak.device.control.InputInjector

/**
 * Exists purely to obtain gesture-dispatch / text-injection capability for
 * InputInjector — this service does not observe or react to UI events, and
 * requires an explicit grant in Settings > Accessibility (not requestable
 * as a normal runtime permission). See docs/DEVICE_CONTROL_PROTOCOL.md.
 */
class DeviceControlAccessibilityService : AccessibilityService() {

    override fun onServiceConnected() {
        super.onServiceConnected()
        InputInjector.attach(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit

    override fun onInterrupt() = Unit

    override fun onDestroy() {
        InputInjector.detach(this)
        super.onDestroy()
    }
}
