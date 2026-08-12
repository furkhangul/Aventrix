package com.furoftheweak.device.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.lifecycle.lifecycleScope
import com.furoftheweak.device.R
import com.furoftheweak.device.accessibility.DeviceControlAccessibilityService
import com.furoftheweak.device.control.ControlForegroundService
import com.furoftheweak.device.databinding.ActivityHomeBinding
import com.furoftheweak.device.net.ApiClientFactory
import com.furoftheweak.device.storage.SecureStore
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * Polling only happens here, while this Activity is on screen and sharing
 * is toggled on — deliberately not an always-on background service. The
 * owner opens the app to actively allow a session, matching this project's
 * explicit-consent posture elsewhere (see plan/DEVICE_CONTROL_PROTOCOL.md).
 */
class HomeActivity : AppCompatActivity() {

    private lateinit var binding: ActivityHomeBinding
    private lateinit var store: SecureStore

    private var sharingEnabled = false
    private var pollingJob: Job? = null
    private var pendingSessionId: String? = null

    private val notificationPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    private val projectionLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            val data = result.data
            if (result.resultCode == RESULT_OK && data != null) {
                startControlService(data, result.resultCode)
            } else {
                // User declined the MediaProjection consent dialog — resume
                // polling so the next session attempt gets another chance.
                startPolling()
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = SecureStore(applicationContext)

        if (!store.isPaired) {
            startActivity(Intent(this, PairingActivity::class.java))
            finish()
            return
        }

        binding = ActivityHomeBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.deviceNameText.text = store.deviceName
        binding.sharingSwitch.setOnCheckedChangeListener { _, checked -> onSharingToggled(checked) }

        binding.unpairButton.setOnClickListener {
            stopPolling()
            store.clearPairing()
            startActivity(Intent(this, PairingActivity::class.java))
            finish()
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    private fun onSharingToggled(checked: Boolean) {
        sharingEnabled = checked
        if (checked) {
            if (!isAccessibilityServiceEnabled()) showAccessibilityPrompt()
            startPolling()
        } else {
            stopPolling()
        }
    }

    private fun startPolling() {
        val baseUrl = store.baseUrl ?: return
        val deviceId = store.deviceId ?: return
        val deviceSecret = store.deviceSecret ?: return

        pollingJob?.cancel()
        pollingJob = lifecycleScope.launch {
            val api = ApiClientFactory.create(baseUrl)
            while (isActive && sharingEnabled) {
                val response = runCatching {
                    api.getPendingSession(deviceId, ApiClientFactory.bearer(deviceSecret))
                }.getOrNull()
                val sessionId = response?.takeIf { it.isSuccessful }?.body()?.sessionId
                if (sessionId != null) {
                    pendingSessionId = sessionId
                    requestProjectionAndStart()
                    return@launch
                }
                delay(POLL_INTERVAL_MS)
            }
        }
    }

    private fun stopPolling() {
        pollingJob?.cancel()
        pollingJob = null
    }

    private fun requestProjectionAndStart() {
        val manager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        projectionLauncher.launch(manager.createScreenCaptureIntent())
    }

    private fun startControlService(projectionData: Intent, resultCode: Int) {
        val sessionId = pendingSessionId ?: return
        pendingSessionId = null

        val serviceIntent = Intent(this, ControlForegroundService::class.java).apply {
            putExtra(ControlForegroundService.EXTRA_RESULT_CODE, resultCode)
            putExtra(ControlForegroundService.EXTRA_RESULT_DATA, projectionData)
            putExtra(ControlForegroundService.EXTRA_SESSION_ID, sessionId)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }

        // Keep listening so a follow-up session can be picked up once this one ends.
        startPolling()
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val expected = "$packageName/${DeviceControlAccessibilityService::class.java.name}"
        val enabled = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
            ?: return false
        return enabled.split(':').any { it.equals(expected, ignoreCase = true) }
    }

    private fun showAccessibilityPrompt() {
        AlertDialog.Builder(this)
            .setTitle(R.string.accessibility_prompt_title)
            .setMessage(R.string.accessibility_prompt_message)
            .setPositiveButton(R.string.accessibility_prompt_open_settings) { _, _ ->
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
            .setNegativeButton(R.string.common_cancel, null)
            .show()
    }

    override fun onDestroy() {
        stopPolling()
        super.onDestroy()
    }

    companion object {
        private const val POLL_INTERVAL_MS = 3000L
    }
}
