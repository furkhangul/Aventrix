package com.aventrix.device.ui

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.aventrix.device.R
import com.aventrix.device.databinding.ActivitySetupBinding
import com.aventrix.device.storage.SecureStore

/** One-time server base URL entry — no fixed prod host exists yet (see DEVICE_CONTROL_PROTOCOL.md). */
class SetupActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySetupBinding
    private lateinit var store: SecureStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = SecureStore(applicationContext)

        if (!store.baseUrl.isNullOrBlank() && store.isPaired) {
            startActivity(Intent(this, HomeActivity::class.java))
            finish()
            return
        }

        binding = ActivitySetupBinding.inflate(layoutInflater)
        setContentView(binding.root)

        store.baseUrl?.let { binding.serverUrlInput.setText(it) }

        binding.continueButton.setOnClickListener { onContinue() }
    }

    private fun onContinue() {
        val raw = binding.serverUrlInput.text?.toString()?.trim().orEmpty()
        if (raw.isEmpty() || !(raw.startsWith("http://") || raw.startsWith("https://"))) {
            binding.serverUrlLayout.error = getString(R.string.setup_invalid_url)
            return
        }
        binding.serverUrlLayout.error = null
        store.baseUrl = raw.trimEnd('/')

        val next = if (store.isPaired) HomeActivity::class.java else PairingActivity::class.java
        startActivity(Intent(this, next))
        finish()
    }
}
