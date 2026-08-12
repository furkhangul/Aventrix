import { ArrowLeft } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { useEndSession, useStartSession } from "@/hooks/use-devices";
import { isApiError } from "@/hooks/use-auth";
import {
  addIceCandidate,
  applyAnswer,
  createAnswer,
  createDeviceConnection,
  SignalingSocket,
  sendInputEvent,
} from "@/lib/webrtc";
import type { DeviceInputMessage } from "@/lib/types";

type ConnectionState = "starting" | "waiting_for_peer" | "connected" | "ended" | "error";

export function DeviceControlPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { deviceId } = useParams<{ deviceId: string }>();
  const startSession = useStartSession(deviceId ?? "");
  const endSession = useEndSession(deviceId ?? "");

  const [state, setState] = useState<ConnectionState>("starting");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const signalingRef = useRef<SignalingSocket | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const startedRef = useRef(false);

  const sendInput = useCallback((message: DeviceInputMessage) => {
    if (dataChannelRef.current) sendInputEvent(dataChannelRef.current, message);
  }, []);

  useEffect(() => {
    if (!deviceId || startedRef.current) return;
    startedRef.current = true;

    let cancelled = false;

    startSession.mutate(undefined, {
      onSuccess: async (session) => {
        if (cancelled) return;
        setSessionId(session.session_id);
        setState("waiting_for_peer");

        const signaling = new SignalingSocket(session.session_id, session.web_ticket);
        signalingRef.current = signaling;
        await signaling.ready();

        const pc = createDeviceConnection({
          iceServers: session.ice_servers,
          onTrack: (stream) => {
            if (videoRef.current) videoRef.current.srcObject = stream;
            setState("connected");
          },
          onDataChannel: (channel) => {
            dataChannelRef.current = channel;
          },
          onIceCandidate: (candidate) => signaling.send({ type: "ice-candidate", data: candidate }),
        });
        pcRef.current = pc;

        signaling.onMessage(async (message) => {
          if (message.type === "offer") {
            const answer = await createAnswer(pc, message.data);
            signaling.send({ type: "answer", data: answer });
          } else if (message.type === "answer") {
            await applyAnswer(pc, message.data);
          } else if (message.type === "ice-candidate") {
            await addIceCandidate(pc, message.data);
          } else if (message.type === "bye") {
            setState("ended");
          }
        });
      },
      onError: () => setState("error"),
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId]);

  const disconnect = useCallback(() => {
    pcRef.current?.close();
    signalingRef.current?.close();
    if (sessionId) endSession.mutate(sessionId);
    navigate("/devices");
  }, [endSession, navigate, sessionId]);

  useEffect(() => {
    return () => {
      pcRef.current?.close();
      signalingRef.current?.close();
    };
  }, []);

  const pointerToNormalized = (event: React.PointerEvent<HTMLVideoElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) / rect.width,
      y: (event.clientY - rect.top) / rect.height,
    };
  };

  if (!deviceId) return null;

  if (state === "error") {
    return (
      <ErrorState
        message={isApiError(startSession.error) ? startSession.error.message : undefined}
        onRetry={() => navigate("/devices")}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/devices")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">{t("devices.controlTitle")}</h1>
            <Badge variant={state === "connected" ? "success" : state === "ended" ? "outline" : "secondary"}>
              {t(`devices.connectionState.${state}`)}
            </Badge>
          </div>
        </div>
        <Button variant="destructive" onClick={disconnect}>
          {t("devices.disconnect")}
        </Button>
      </div>

      <div className="flex items-center justify-center rounded-xl border border-border bg-black/90 p-4">
        {state === "starting" || state === "waiting_for_peer" ? (
          <div className="flex aspect-[9/16] w-full max-w-xs items-center justify-center">
            <LoadingState label={t("devices.waitingForDevice")} />
          </div>
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="max-h-[70vh] w-auto max-w-full cursor-crosshair rounded-md"
            onPointerDown={(e) => sendInput({ type: "pointer", action: "down", ...pointerToNormalized(e) })}
            onPointerMove={(e) => {
              if (e.buttons > 0) sendInput({ type: "pointer", action: "move", ...pointerToNormalized(e) });
            }}
            onPointerUp={(e) => sendInput({ type: "pointer", action: "up", ...pointerToNormalized(e) })}
          />
        )}
      </div>
      <p className="text-center text-xs text-muted-foreground">{t("devices.controlHint")}</p>
    </div>
  );
}
