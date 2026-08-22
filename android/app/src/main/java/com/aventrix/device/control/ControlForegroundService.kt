package com.aventrix.device.control

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.media.projection.MediaProjection
import android.os.Build
import android.os.IBinder
import android.util.DisplayMetrics
import android.util.Log
import android.view.WindowManager
import androidx.core.app.NotificationCompat
import com.aventrix.device.R
import com.aventrix.device.net.ApiClientFactory
import com.aventrix.device.net.DeviceWsTicketResponse
import com.aventrix.device.net.SessionTokenRequest
import com.aventrix.device.net.SignalMessage
import com.aventrix.device.net.SignalingListener
import com.aventrix.device.net.SignalingSocket
import com.aventrix.device.storage.SecureStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import org.webrtc.DataChannel
import org.webrtc.DefaultVideoDecoderFactory
import org.webrtc.DefaultVideoEncoderFactory
import org.webrtc.EglBase
import org.webrtc.IceCandidate
import org.webrtc.MediaConstraints
import org.webrtc.MediaStream
import org.webrtc.PeerConnection
import org.webrtc.PeerConnectionFactory
import org.webrtc.RtpReceiver
import org.webrtc.ScreenCapturerAndroid
import org.webrtc.SdpObserver
import org.webrtc.SessionDescription
import org.webrtc.SurfaceTextureHelper
import org.webrtc.VideoSource
import org.webrtc.VideoTrack
import java.nio.charset.StandardCharsets

/**
 * Owns one active control session end to end: takes the MediaProjection
 * consent result + a session_id from HomeActivity, exchanges it for a
 * signaling ticket, connects the WS signaling socket, captures the screen
 * via MediaProjection into a WebRTC video track, offers it (device is
 * always the offering side per docs/DEVICE_CONTROL_PROTOCOL.md), and relays
 * "input" DataChannel messages to InputInjector. Foreground + a persistent
 * notification for the whole session per Android 14+'s MediaProjection
 * requirement (see docs/DEVICE_CONTROL_PROTOCOL.md's Android client section).
 */
class ControlForegroundService : Service() {

    private val job = Job()
    private val scope = CoroutineScope(Dispatchers.Main + job)
    private val json = Json { ignoreUnknownKeys = true }

    private lateinit var store: SecureStore

    private var eglBase: EglBase? = null
    private var peerConnectionFactory: PeerConnectionFactory? = null
    private var peerConnection: PeerConnection? = null
    private var videoSource: VideoSource? = null
    private var videoTrack: VideoTrack? = null
    private var dataChannel: DataChannel? = null
    private var signaling: SignalingSocket? = null
    private var capturer: ScreenCapturerAndroid? = null
    private var tornDown = false

    override fun onCreate() {
        super.onCreate()
        store = SecureStore(applicationContext)
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val resultCode = intent?.getIntExtra(EXTRA_RESULT_CODE, 0) ?: 0
        val projectionData = intent?.getParcelableExtra<Intent>(EXTRA_RESULT_DATA)
        val sessionId = intent?.getStringExtra(EXTRA_SESSION_ID)

        if (projectionData == null || sessionId == null || resultCode != Activity.RESULT_OK) {
            Log.e(TAG, "Missing/invalid projection result or session id — stopping")
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground(NOTIFICATION_ID, buildNotification(), foregroundServiceType())
        startSession(sessionId, projectionData)
        return START_NOT_STICKY
    }

    private fun foregroundServiceType(): Int =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION else 0

    private fun startSession(sessionId: String, projectionData: Intent) {
        val baseUrl = store.baseUrl
        val deviceId = store.deviceId
        val deviceSecret = store.deviceSecret
        if (baseUrl == null || deviceId == null || deviceSecret == null) {
            Log.e(TAG, "Not paired — stopping")
            stopSelf()
            return
        }

        scope.launch {
            val api = ApiClientFactory.create(baseUrl)
            val response = runCatching {
                api.issueSessionToken(deviceId, SessionTokenRequest(sessionId), ApiClientFactory.bearer(deviceSecret))
            }.getOrNull()

            val ticket = response?.takeIf { it.isSuccessful }?.body()
            if (ticket == null) {
                Log.e(TAG, "Failed to obtain session ticket (HTTP ${response?.code()})")
                stopSelf()
                return@launch
            }

            setupPeerConnection(ticket, projectionData)
            val wsUrl = "${ApiClientFactory.toWebSocketBase(baseUrl)}/api/v1/devices/sessions/$sessionId/signal?ticket=${ticket.ticket}"
            signaling = SignalingSocket(wsUrl, object : SignalingListener {
                override fun onOpen() {
                    Log.i(TAG, "Signaling connected")
                    createOfferAndSend()
                }
                override fun onMessage(message: SignalMessage) = handleSignal(message)
                override fun onClosed(code: Int, reason: String) {
                    Log.i(TAG, "Signaling closed: $code $reason")
                    scope.launch { teardown() }
                }
                override fun onFailure(t: Throwable) {
                    Log.e(TAG, "Signaling failure", t)
                    scope.launch { teardown() }
                }
            }).also { it.connect() }
        }
    }

    private fun setupPeerConnection(ticket: DeviceWsTicketResponse, projectionData: Intent) {
        val eglBaseInstance = EglBase.create().also { eglBase = it }

        PeerConnectionFactory.initialize(
            PeerConnectionFactory.InitializationOptions.builder(applicationContext).createInitializationOptions()
        )
        val factory = PeerConnectionFactory.builder()
            .setVideoEncoderFactory(DefaultVideoEncoderFactory(eglBaseInstance.eglBaseContext, true, true))
            .setVideoDecoderFactory(DefaultVideoDecoderFactory(eglBaseInstance.eglBaseContext))
            .createPeerConnectionFactory()
        peerConnectionFactory = factory

        val iceServers = ticket.iceServers.map { server ->
            val builder = PeerConnection.IceServer.builder(server.urls)
            server.username?.let { builder.setUsername(it) }
            server.credential?.let { builder.setPassword(it) }
            builder.createIceServer()
        }
        val rtcConfig = PeerConnection.RTCConfiguration(iceServers)

        val pc = factory.createPeerConnection(rtcConfig, object : PeerConnection.Observer {
            override fun onIceCandidate(candidate: IceCandidate) {
                signaling?.send(iceCandidateMessage(candidate))
            }
            override fun onConnectionChange(newState: PeerConnection.PeerConnectionState) {
                Log.i(TAG, "Peer connection state: $newState")
                if (newState == PeerConnection.PeerConnectionState.FAILED ||
                    newState == PeerConnection.PeerConnectionState.CLOSED
                ) {
                    scope.launch { teardown() }
                }
            }
            override fun onDataChannel(channel: DataChannel) = Unit
            override fun onIceConnectionChange(state: PeerConnection.IceConnectionState) = Unit
            override fun onIceConnectionReceivingChange(receiving: Boolean) = Unit
            override fun onIceGatheringChange(state: PeerConnection.IceGatheringState) = Unit
            override fun onIceCandidatesRemoved(candidates: Array<out IceCandidate>) = Unit
            override fun onAddStream(stream: MediaStream) = Unit
            override fun onRemoveStream(stream: MediaStream) = Unit
            override fun onSignalingChange(state: PeerConnection.SignalingState) = Unit
            override fun onRenegotiationNeeded() = Unit
            override fun onAddTrack(receiver: RtpReceiver, streams: Array<out MediaStream>) = Unit
        }) ?: run {
            Log.e(TAG, "createPeerConnection returned null")
            stopSelf()
            return
        }
        peerConnection = pc

        val displayMetrics = DisplayMetrics()
        @Suppress("DEPRECATION")
        (getSystemService(WINDOW_SERVICE) as WindowManager).defaultDisplay.getRealMetrics(displayMetrics)
        InputInjector.displayWidth = displayMetrics.widthPixels
        InputInjector.displayHeight = displayMetrics.heightPixels

        val surfaceTextureHelper = SurfaceTextureHelper.create("CaptureThread", eglBaseInstance.eglBaseContext)
        val source = factory.createVideoSource(true).also { videoSource = it }

        // ScreenCapturerAndroid manages its own MediaProjection internally
        // from the raw consent Intent — this is the standard org.webrtc API
        // (matches Google's AppRTCMobile reference usage); double check
        // against whatever version Android Studio actually resolves, since
        // this couldn't be compiled in the authoring environment.
        val screenCapturer = ScreenCapturerAndroid(projectionData, object : MediaProjection.Callback() {
            override fun onStop() {
                Log.i(TAG, "Screen capture stopped (system or user revoked)")
                scope.launch { teardown() }
            }
        }).also { capturer = it }
        screenCapturer.initialize(surfaceTextureHelper, applicationContext, source.capturerObserver)
        screenCapturer.startCapture(displayMetrics.widthPixels, displayMetrics.heightPixels, 30)

        val track = factory.createVideoTrack("screen0", source).also { videoTrack = it }
        pc.addTrack(track, listOf("aventrix-stream"))

        val channel = pc.createDataChannel("input", DataChannel.Init()).also { dataChannel = it }
        channel.registerObserver(object : DataChannel.Observer {
            override fun onBufferedAmountChange(previousAmount: Long) = Unit
            override fun onStateChange() = Unit
            override fun onMessage(buffer: DataChannel.Buffer) {
                val bytes = ByteArray(buffer.data.remaining())
                buffer.data.get(bytes)
                handleInputMessage(String(bytes, StandardCharsets.UTF_8))
            }
        })
    }

    private fun handleInputMessage(text: String) {
        val message = runCatching { json.decodeFromString(DeviceInputMessage.serializer(), text) }.getOrNull() ?: return
        when (message.type) {
            "pointer" -> InputInjector.handlePointer(message)
            "key" -> InputInjector.handleKey(message)
        }
    }

    private fun createOfferAndSend() {
        val pc = peerConnection ?: return
        pc.createOffer(object : SdpObserver {
            override fun onCreateSuccess(desc: SessionDescription) {
                pc.setLocalDescription(object : SdpObserver {
                    override fun onCreateSuccess(ignored: SessionDescription?) = Unit
                    override fun onSetSuccess() {
                        signaling?.send(sdpMessage("offer", desc))
                    }
                    override fun onCreateFailure(error: String?) = Unit
                    override fun onSetFailure(error: String?) {
                        Log.e(TAG, "setLocalDescription failed: $error")
                    }
                }, desc)
            }
            override fun onSetSuccess() = Unit
            override fun onCreateFailure(error: String?) {
                Log.e(TAG, "createOffer failed: $error")
            }
            override fun onSetFailure(error: String?) = Unit
        }, MediaConstraints())
    }

    private fun handleSignal(message: SignalMessage) {
        val pc = peerConnection ?: return
        when (message.type) {
            "answer" -> {
                val sdp = message.data.jsonObject["sdp"]?.jsonPrimitive?.content ?: return
                pc.setRemoteDescription(object : SdpObserver {
                    override fun onCreateSuccess(ignored: SessionDescription?) = Unit
                    override fun onSetSuccess() = Unit
                    override fun onCreateFailure(error: String?) = Unit
                    override fun onSetFailure(error: String?) {
                        Log.e(TAG, "setRemoteDescription(answer) failed: $error")
                    }
                }, SessionDescription(SessionDescription.Type.ANSWER, sdp))
            }
            "ice-candidate" -> {
                val data = message.data.jsonObject
                val candidate = data["candidate"]?.jsonPrimitive?.content ?: return
                val sdpMid = data["sdpMid"]?.jsonPrimitive?.content
                val sdpMLineIndex = data["sdpMLineIndex"]?.jsonPrimitive?.content?.toIntOrNull() ?: 0
                pc.addIceCandidate(IceCandidate(sdpMid, sdpMLineIndex, candidate))
            }
            "bye" -> scope.launch { teardown() }
        }
    }

    private fun sdpMessage(type: String, desc: SessionDescription) = SignalMessage(
        type = type,
        data = buildJsonObject {
            put("type", type)
            put("sdp", desc.description)
        },
    )

    private fun iceCandidateMessage(candidate: IceCandidate) = SignalMessage(
        type = "ice-candidate",
        data = buildJsonObject {
            put("candidate", candidate.sdp)
            put("sdpMid", candidate.sdpMid)
            put("sdpMLineIndex", candidate.sdpMLineIndex)
        },
    )

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                getString(R.string.control_notification_channel_name),
                NotificationManager.IMPORTANCE_LOW,
            )
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    private fun buildNotification(): Notification =
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.control_notification_title))
            .setContentText(getString(R.string.control_notification_text))
            .setSmallIcon(R.drawable.ic_screen_share)
            .setOngoing(true)
            .build()

    private fun teardown() {
        if (tornDown) return
        tornDown = true
        signaling?.close()
        signaling = null
        dataChannel?.close()
        dataChannel = null
        peerConnection?.close()
        peerConnection = null
        capturer?.stopCapture()
        capturer = null
        videoTrack?.dispose()
        videoTrack = null
        videoSource?.dispose()
        videoSource = null
        peerConnectionFactory?.dispose()
        peerConnectionFactory = null
        eglBase?.release()
        eglBase = null
        InputInjector.displayWidth = 0
        InputInjector.displayHeight = 0
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        teardown()
        job.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        private const val TAG = "ControlService"
        private const val CHANNEL_ID = "device_control"
        private const val NOTIFICATION_ID = 42
        const val EXTRA_RESULT_CODE = "result_code"
        const val EXTRA_RESULT_DATA = "result_data"
        const val EXTRA_SESSION_ID = "session_id"
    }
}
