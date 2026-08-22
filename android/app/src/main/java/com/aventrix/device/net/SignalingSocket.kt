package com.aventrix.device.net

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

/** One JSON frame per WS message — matches the SignalMessage TypeScript type in docs/DEVICE_CONTROL_PROTOCOL.md. */
@Serializable
data class SignalMessage(
    val type: String,
    val data: JsonElement,
)

interface SignalingListener {
    fun onOpen()
    fun onMessage(message: SignalMessage)
    fun onClosed(code: Int, reason: String)
    fun onFailure(t: Throwable)
}

/**
 * WS /api/v1/devices/sessions/{session_id}/signal?ticket=<device_ticket>.
 * A dedicated OkHttpClient (not the REST one) — long/no read timeout, since
 * this socket is meant to stay open for the whole control session.
 */
class SignalingSocket(
    private val wsUrl: String,
    private val listener: SignalingListener,
) {
    private val json = Json { ignoreUnknownKeys = true }
    private val client = OkHttpClient.Builder()
        .pingInterval(20, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()
    private var socket: WebSocket? = null

    fun connect() {
        val request = Request.Builder().url(wsUrl).build()
        socket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                listener.onOpen()
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                runCatching { json.decodeFromString(SignalMessage.serializer(), text) }
                    .onSuccess { listener.onMessage(it) }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                listener.onClosed(code, reason)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                listener.onFailure(t)
            }
        })
    }

    fun send(message: SignalMessage) {
        socket?.send(json.encodeToString(SignalMessage.serializer(), message))
    }

    fun close() {
        socket?.close(1000, "bye")
        socket = null
        client.dispatcher.executorService.shutdown()
    }
}
