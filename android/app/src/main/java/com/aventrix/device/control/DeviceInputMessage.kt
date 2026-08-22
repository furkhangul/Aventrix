package com.aventrix.device.control

import kotlinx.serialization.Serializable

/** Mirrors the DeviceInputMessage TypeScript type in docs/DEVICE_CONTROL_PROTOCOL.md. */
@Serializable
data class DeviceInputMessage(
    val type: String, // "pointer" | "key"
    val action: String, // pointer: "down"|"move"|"up" — key: "down"|"up"
    val x: Float? = null, // pointer only, normalized [0,1]
    val y: Float? = null, // pointer only, normalized [0,1]
    val key: String? = null, // key only
    val code: String? = null, // key only
)
