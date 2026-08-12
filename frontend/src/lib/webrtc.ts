import type { DeviceInputMessage, IceServer, SignalMessage } from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

/**
 * Wraps the /signal WebSocket with a typed send/receive surface matching
 * the SignalMessage envelope both peers (and, eventually, the Android
 * client) must agree on — see docs/DEVICE_CONTROL_PROTOCOL.md.
 */
export class SignalingSocket {
  private ws: WebSocket;
  private messageHandlers = new Set<(message: SignalMessage) => void>();
  private openPromise: Promise<void>;

  constructor(sessionId: string, ticket: string) {
    const base = API_BASE || window.location.origin;
    const wsProtocol = base.startsWith("https") ? "wss" : "ws";
    const httpUrl = new URL(`/api/v1/devices/sessions/${sessionId}/signal`, base);
    const url = `${wsProtocol}://${httpUrl.host}${httpUrl.pathname}?ticket=${encodeURIComponent(ticket)}`;

    this.ws = new WebSocket(url);
    this.openPromise = new Promise((resolve, reject) => {
      this.ws.addEventListener("open", () => resolve(), { once: true });
      this.ws.addEventListener("error", () => reject(new Error("Signaling connection failed")), { once: true });
    });
    this.ws.addEventListener("message", (event) => {
      try {
        const message = JSON.parse(event.data) as SignalMessage;
        this.messageHandlers.forEach((handler) => handler(message));
      } catch {
        // Ignore malformed frames rather than crashing the session.
      }
    });
  }

  async ready(): Promise<void> {
    return this.openPromise;
  }

  onMessage(handler: (message: SignalMessage) => void): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  send(message: SignalMessage): void {
    this.ws.send(JSON.stringify(message));
  }

  close(): void {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.send({ type: "bye", data: {} });
    }
    this.ws.close();
  }
}

export interface DeviceConnectionHandlers {
  iceServers: IceServer[];
  onTrack?: (stream: MediaStream) => void;
  onDataChannel?: (channel: RTCDataChannel) => void;
  onIceCandidate?: (candidate: RTCIceCandidateInit) => void;
}

export function createDeviceConnection(handlers: DeviceConnectionHandlers): RTCPeerConnection {
  const pc = new RTCPeerConnection({
    iceServers: handlers.iceServers.map((server) => ({
      urls: server.urls,
      username: server.username ?? undefined,
      credential: server.credential ?? undefined,
    })),
  });

  pc.addEventListener("track", (event) => {
    if (event.streams[0]) handlers.onTrack?.(event.streams[0]);
  });
  pc.addEventListener("datachannel", (event) => handlers.onDataChannel?.(event.channel));
  pc.addEventListener("icecandidate", (event) => {
    if (event.candidate) handlers.onIceCandidate?.(event.candidate.toJSON());
  });

  return pc;
}

export async function createOffer(pc: RTCPeerConnection): Promise<RTCSessionDescriptionInit> {
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  return offer;
}

export async function createAnswer(
  pc: RTCPeerConnection,
  offer: RTCSessionDescriptionInit,
): Promise<RTCSessionDescriptionInit> {
  await pc.setRemoteDescription(offer);
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  return answer;
}

export async function applyAnswer(pc: RTCPeerConnection, answer: RTCSessionDescriptionInit): Promise<void> {
  await pc.setRemoteDescription(answer);
}

export async function addIceCandidate(pc: RTCPeerConnection, candidate: RTCIceCandidateInit): Promise<void> {
  await pc.addIceCandidate(candidate);
}

/** Sends a normalized-coordinate pointer/key event over the "input" data channel. */
export function sendInputEvent(channel: RTCDataChannel, message: DeviceInputMessage): void {
  if (channel.readyState === "open") {
    channel.send(JSON.stringify(message));
  }
}
