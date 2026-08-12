package com.furoftheweak.device.ui

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.furoftheweak.device.R
import com.furoftheweak.device.databinding.ActivityPairingBinding
import com.furoftheweak.device.net.ApiClientFactory
import com.furoftheweak.device.net.PairingExchangeRequest
import com.furoftheweak.device.storage.SecureStore
import kotlinx.coroutines.launch

/**
 * Manual 8-character code entry (see backend/app/utils/short_code.py) — no
 * camera/QR scanning in v1. POST /pairing-codes/{code}/exchange, per
 * docs/DEVICE_CONTROL_PROTOCOL.md.
 */
class PairingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityPairingBinding
    private lateinit var store: SecureStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPairingBinding.inflate(layoutInflater)
        setContentView(binding.root)
        store = SecureStore(applicationContext)

        binding.deviceNameInput.setText(Build.MODEL ?: "Android device")
        binding.pairButton.setOnClickListener { attemptPairing() }
    }

    private fun attemptPairing() {
        val baseUrl = store.baseUrl
        if (baseUrl.isNullOrBlank()) {
            startActivity(Intent(this, SetupActivity::class.java))
            finish()
            return
        }

        val code = binding.codeInput.text?.toString()?.trim().orEmpty()
        val deviceName = binding.deviceNameInput.text?.toString()?.trim().orEmpty()
        if (code.length < 4 || deviceName.isEmpty()) {
            binding.codeLayout.error = getString(R.string.pairing_invalid_code)
            return
        }
        binding.codeLayout.error = null
        binding.pairButton.isEnabled = false

        // ANDROID_ID: no dangerous permission, not hardware-identifying, and
        // resets on factory reset — correct behavior for a "stable per-install
        // id" credential (see docs/DEVICE_CONTROL_PROTOCOL.md), not a bug.
        val fingerprint = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"

        lifecycleScope.launch {
            val api = ApiClientFactory.create(baseUrl)
            val response = runCatching {
                api.exchangePairingCode(
                    code,
                    PairingExchangeRequest(code = code, deviceName = deviceName, deviceFingerprint = fingerprint),
                )
            }.getOrNull()

            binding.pairButton.isEnabled = true
            val body = response?.takeIf { it.isSuccessful }?.body()
            if (body == null) {
                binding.codeLayout.error = getString(R.string.pairing_failed)
                return@launch
            }

            store.deviceId = body.device.id
            store.deviceSecret = body.deviceSecret
            store.deviceName = body.device.name

            startActivity(Intent(this@PairingActivity, HomeActivity::class.java))
            finish()
        }
    }
}
