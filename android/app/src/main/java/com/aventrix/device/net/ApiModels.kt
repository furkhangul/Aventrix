package com.aventrix.device.net

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Mirrors backend/app/schemas/device.py — keep both in sync; that file (and
// docs/DEVICE_CONTROL_PROTOCOL.md) is the source of truth for this contract.

@Serializable
data class PairingExchangeRequest(
    val code: String,
    @SerialName("device_name") val deviceName: String,
    @SerialName("device_fingerprint") val deviceFingerprint: String,
    val platform: String = "android",
)

@Serializable
data class DevicePublic(
    val id: String,
    val name: String,
    val platform: String,
    @SerialName("is_active") val isActive: Boolean,
)

@Serializable
data class PairingExchangeResponse(
    val device: DevicePublic,
    @SerialName("device_secret") val deviceSecret: String,
)

@Serializable
data class IceServer(
    val urls: String,
    val username: String? = null,
    val credential: String? = null,
)

@Serializable
data class PendingSessionResponse(
    @SerialName("session_id") val sessionId: String? = null,
)

@Serializable
data class SessionTokenRequest(
    @SerialName("session_id") val sessionId: String,
)

@Serializable
data class DeviceWsTicketResponse(
    val ticket: String,
    @SerialName("ice_servers") val iceServers: List<IceServer>,
    @SerialName("expires_in") val expiresIn: Int,
)
