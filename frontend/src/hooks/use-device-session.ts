import { useCallback, useEffect, useRef, useState } from "react";
import { useStartSession } from "@/hooks/use-devices";
import { api } from "@/lib/api";
import { isApiError } from "@/hooks/use-auth";
import {
  createAnswer,
  createDeviceConnection,
  IceCandidateQueue,
  sendInputEvent,
  SignalingError,
  SignalingSocket,
  WS_SESSION_NOT_FOUND,
  WS_TICKET_REJECTED,
} from "@/lib/webrtc";
import type { DeviceInputMessage, DeviceNavKey, DeviceSessionStart } from "@/lib/types";

/**
 * Drives one remote-control session from "press connect" to teardown.
 *
 * The phase is deliberately finer-grained than the old starting/waiting/
 * connected triple: each of these steps can stall for a different reason,
 * and "waiting for device" covering all of them is why a failed session used
 * to look identical to a slow one — an indefinite spinner either way. Each
 * stall now has its own deadline and its own error code, so the page can say
 * what went wrong and offer the right way out.
 */
export type DeviceSessionPhase =
  | "idle"
  | "starting"
  | "waiting_for_device"
  | "negotiating"
  | "connected"
  | "ended"
  | "error";

export type DeviceSessionErrorCode =
  | "start_failed"
  | "not_enabled"
  | "device_offline"
  | "signaling_failed"
  | "ticket_rejected"
  | "session_gone"
  | "device_timeout"
  | "negotiation_timeout"
  | "peer_failed"
  | "connection_lost";

export interface DeviceSessionStats {
  width: number;
  height: number;
  framesPerSecond: number;
  kilobitsPerSecond: number;
  roundTripMs: number | null;
}

/** How long each stalled phase waits before it is reported as a failure. */
const DEVICE_JOIN_TIMEOUT_MS = 45_000;
const NEGOTIATION_TIMEOUT_MS = 30_000;
const STATS_INTERVAL_MS = 2_000;

export interface UseDeviceSessionResult {
  phase: DeviceSessionPhase;
  errorCode: DeviceSessionErrorCode | null;
  sessionId: string | null;
  stream: MediaStream | null;
  stats: DeviceSessionStats | null;
  /** True once the "input" data channel is open, i.e. touch input will land. */
  canSendInput: boolean;
  connect: () => void;
  disconnect: () => void;
  sendInput: (message: DeviceInputMessage) => void;
  sendNavKey: (key: DeviceNavKey) => void;
}

export function useDeviceSession(deviceId: string | undefined): UseDeviceSessionResult {
  const startSession = useStartSession(deviceId ?? "");
  const startSessionRef = useRef(startSession);
  startSessionRef.current = startSession;

  const [phase, setPhase] = useState<DeviceSessionPhase>("idle");
  const [errorCode, setErrorCode] = useState<DeviceSessionErrorCode | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [stats, setStats] = useState<DeviceSessionStats | null>(null);
  const [canSendInput, setCanSendInput] = useState(false);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const signalingRef = useRef<SignalingSocket | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const generationRef = useRef(0);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  }, []);

  /**
   * Tears down everything this attempt owns. [generationRef] is bumped so any
   * in-flight async step from the previous attempt — an awaited socket open, a
   * queued setRemoteDescription — resolves into a no-op instead of writing
   * state belonging to a session the user already left.
   */
  const teardown = useCallback(() => {
    generationRef.current += 1;
    clearTimers();
    dataChannelRef.current?.close();
    dataChannelRef.current = null;
    signalingRef.current?.close();
    signalingRef.current = null;
    pcRef.current?.getReceivers().forEach((receiver) => receiver.track?.stop());
    pcRef.current?.close();
    pcRef.current = null;
    setStream(null);
    setStats(null);
    setCanSendInput(false);
  }, [clearTimers]);

  const fail = useCallback(
    (code: DeviceSessionErrorCode) => {
      teardown();
      setErrorCode(code);
      setPhase("error");
    },
    [teardown],
  );

  const disconnect = useCallback(() => {
    const id = sessionIdRef.current;
    teardown();
    setPhase("ended");
    setErrorCode(null);
    if (deviceId && id) {
      // Fire-and-forget: closing our socket already told the phone to stop;
      // this only records the reason on the session row.
      api.post(`/api/v1/devices/${deviceId}/sessions/${id}/end`).catch(() => undefined);
    }
    sessionIdRef.current = null;
  }, [deviceId, teardown]);

  const connect = useCallback(() => {
    if (!deviceId) return;
    teardown();
    setErrorCode(null);
    setPhase("starting");

    const generation = generationRef.current;
    const isStale = () => generationRef.current !== generation;

    startSessionRef.current.mutate(undefined, {
      onError: (error) => {
        if (isStale()) return;
        if (isApiError(error) && error.status === 404) fail("not_enabled");
        else if (isApiError(error) && error.status === 409) fail("device_offline");
        else fail("start_failed");
      },
      onSuccess: async (session: DeviceSessionStart) => {
        if (isStale()) return;
        sessionIdRef.current = session.session_id;
        setSessionId(session.session_id);

        const signaling = new SignalingSocket(session.session_id, session.web_ticket);
        signalingRef.current = signaling;

        const pc = createDeviceConnection({
          iceServers: session.ice_servers,
          onIceCandidate: (candidate) => signaling.send({ type: "ice-candidate", data: candidate }),
          onTrack: (mediaStream) => {
            if (isStale()) return;
            clearTimers();
            setStream(mediaStream);
            setPhase("connected");
          },
          onDataChannel: (channel) => {
            dataChannelRef.current = channel;
            const sync = () => {
              if (!isStale()) setCanSendInput(channel.readyState === "open");
            };
            channel.addEventListener("open", sync);
            channel.addEventListener("close", sync);
            sync();
          },
          onConnectionStateChange: (state) => {
            if (isStale()) return;
            if (state === "failed") fail("peer_failed");
            else if (state === "disconnected") fail("connection_lost");
          },
        });
        pcRef.current = pc;
        const iceQueue = new IceCandidateQueue(pc);

        // Handlers go on before the open is awaited: the relay replays the
        // phone's queued offer the instant we subscribe, which can land in
        // the same tick the socket opens.
        signaling.onMessage(async (message) => {
          if (isStale()) return;
          try {
            if (message.type === "peer-joined") {
              clearTimers();
              setPhase((current) => (current === "connected" ? current : "negotiating"));
              timersRef.current.push(
                setTimeout(() => {
                  if (!isStale()) fail("negotiation_timeout");
                }, NEGOTIATION_TIMEOUT_MS),
              );
            } else if (message.type === "offer") {
              const answer = await createAnswer(pc, message.data);
              await iceQueue.remoteDescriptionSet();
              signaling.send({ type: "answer", data: answer });
            } else if (message.type === "answer") {
              await pc.setRemoteDescription(message.data);
              await iceQueue.remoteDescriptionSet();
            } else if (message.type === "ice-candidate") {
              await iceQueue.add(message.data);
            } else if (message.type === "peer-left" || message.type === "bye") {
              teardown();
              setPhase("ended");
            }
          } catch {
            fail("peer_failed");
          }
        });

        signaling.onClose(() => {
          if (isStale()) return;
          // Media may still be flowing peer-to-peer, but with no signaling
          // channel the session can no longer recover from anything.
          teardown();
          setPhase("ended");
        });

        try {
          await signaling.ready();
        } catch (error) {
          if (isStale()) return;
          const code = error instanceof SignalingError ? error.code : undefined;
          if (code === WS_TICKET_REJECTED) fail("ticket_rejected");
          else if (code === WS_SESSION_NOT_FOUND) fail("session_gone");
          else fail("signaling_failed");
          return;
        }

        if (isStale()) return;
        setPhase((current) => (current === "starting" ? "waiting_for_device" : current));
        timersRef.current.push(
          setTimeout(() => {
            if (!isStale()) fail("device_timeout");
          }, DEVICE_JOIN_TIMEOUT_MS),
        );
      },
    });
  }, [deviceId, fail, teardown, clearTimers]);

  // Live quality readout, so a connection that is up but unusable (a stalled
  // relay, a 2 fps encode) looks different from a healthy one.
  useEffect(() => {
    if (phase !== "connected") return;
    const pc = pcRef.current;
    if (!pc) return;

    let previousBytes = 0;
    let previousAt = performance.now();

    const interval = setInterval(async () => {
      const report = await pc.getStats().catch(() => null);
      if (!report) return;

      let next: DeviceSessionStats | null = null;
      let roundTripMs: number | null = null;

      report.forEach((entry) => {
        if (entry.type === "inbound-rtp" && entry.kind === "video") {
          const now = performance.now();
          const elapsedSeconds = (now - previousAt) / 1000;
          const bytes: number = entry.bytesReceived ?? 0;
          const kilobitsPerSecond =
            elapsedSeconds > 0
              ? Math.max(0, Math.round(((bytes - previousBytes) * 8) / 1000 / elapsedSeconds))
              : 0;
          previousBytes = bytes;
          previousAt = now;
          next = {
            width: entry.frameWidth ?? 0,
            height: entry.frameHeight ?? 0,
            framesPerSecond: Math.round(entry.framesPerSecond ?? 0),
            kilobitsPerSecond,
            roundTripMs: null,
          };
        }
        if (entry.type === "candidate-pair" && entry.state === "succeeded" && entry.currentRoundTripTime != null) {
          roundTripMs = Math.round(entry.currentRoundTripTime * 1000);
        }
      });

      if (next) setStats({ ...(next as DeviceSessionStats), roundTripMs });
    }, STATS_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [phase]);

  // Leaving the page must not leave the phone sharing its screen.
  useEffect(() => teardown, [teardown]);

  const sendInput = useCallback((message: DeviceInputMessage) => {
    const channel = dataChannelRef.current;
    if (channel) sendInputEvent(channel, message);
  }, []);

  const sendNavKey = useCallback(
    (key: DeviceNavKey) => {
      sendInput({ type: "key", action: "down", key, code: key });
      sendInput({ type: "key", action: "up", key, code: key });
    },
    [sendInput],
  );

  return {
    phase,
    errorCode,
    sessionId,
    stream,
    stats,
    canSendInput,
    connect,
    disconnect,
    sendInput,
    sendNavKey,
  };
}
