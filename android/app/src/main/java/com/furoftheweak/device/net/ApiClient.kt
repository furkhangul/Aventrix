package com.furoftheweak.device.net

import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Response
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import java.util.concurrent.TimeUnit

/** Only the handful of endpoints the Android client needs — see docs/DEVICE_CONTROL_PROTOCOL.md. */
interface DeviceApi {

    @POST("api/v1/devices/pairing-codes/{code}/exchange")
    suspend fun exchangePairingCode(
        @Path("code") code: String,
        @Body body: PairingExchangeRequest,
    ): Response<PairingExchangeResponse>

    @GET("api/v1/devices/{deviceId}/sessions/pending")
    suspend fun getPendingSession(
        @Path("deviceId") deviceId: String,
        @Header("Authorization") authorization: String,
    ): Response<PendingSessionResponse>

    @POST("api/v1/devices/{deviceId}/sessions/token")
    suspend fun issueSessionToken(
        @Path("deviceId") deviceId: String,
        @Body body: SessionTokenRequest,
        @Header("Authorization") authorization: String,
    ): Response<DeviceWsTicketResponse>
}

object ApiClientFactory {

    private val json = Json { ignoreUnknownKeys = true }

    /** [baseUrl] is whatever the user entered in Setup — e.g. an https:// tunnel or LAN http:// dev server. */
    fun create(baseUrl: String): DeviceApi {
        val normalized = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .build()
        val retrofit = Retrofit.Builder()
            .baseUrl(normalized)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
        return retrofit.create(DeviceApi::class.java)
    }

    fun bearer(secret: String) = "Bearer $secret"

    /** http(s):// base URL -> ws(s):// signaling base, matching the protocol doc's WS URL pattern. */
    fun toWebSocketBase(baseUrl: String): String =
        baseUrl.trimEnd('/').replaceFirst("https://", "wss://").replaceFirst("http://", "ws://")
}
