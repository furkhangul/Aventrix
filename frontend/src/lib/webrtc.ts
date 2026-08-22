import type { DeviceInputMessage, IceServer, SignalMessage } from "@/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export function signalingUrl(sessionId: string, ticket: string): string {
  const base = API_BASE || window.location.origin;
  const httpUrl = new URL(`/api/v1/devices/sessions/${sessionId}/signal`, base);
  const wsProtocol = httpUrl.protocol === "https:" ? "wss" : "ws";
  return `${wsProtocol}://${httpUrl.host}${httpUrl.pathname}?ticket=${encodeURIComponent(ticket)}`;
}

/**
 * Wraps the /signal WebSocket with a typed send/receive surface matching
 * the SignalMessage envelope both peers agree on — see
 * docs/DEVICE_CONTROL_PROTOCOL.md.
 *
 * Frames that arrive before a handler is attached are held, not dropped.
 * The caller has to await the socket opening and build an RTCPeerConnection
 * before it can do anything useful with a message, and the backend now
 * replays everything the phone queued the instant we subscribe — so without
 * this the very first burst (peer-joined, then the offer) could land in that
 * gap and the page would wait forever for an offer that had already come.
 */
export class SignalingSocket {
  private ws: WebSocket;
  private messageHandlers = new Set<(message: SignalMessage) => void>();
  private pending: SignalMessage[] = [];
  private openPromise: Promise<void>;
  private closedHandlers = new Set<(event: CloseEvent) => void>();
  private closedByUs = false;

  constructor(sessionId: string, ticket: string) {
    this.ws = new WebSocket(signalingUrl(sessionId, ticket));

    this.openPromise = new Promise((resolve, reject) => {
      this.ws.addEventListener("open", () => resolve(), { once: true });
      // A rejected handshake surfaces as "close" with no prior "open"; the
      // "error" event carries no detail, so the close code is what tells us
      // whether the ticket was refused (4401) or the session is gone (4404).
      this.ws.addEventListener(
        "close",
        (event) => reject(new SignalingError("Signaling connection failed", event.code)),
        { once: true },
      );
    });

    this.ws.addEventListener("message", (event) => {
      let message: SignalMessage;
      try {
        message = JSON.parse(event.data) as SignalMessage;
      } catch {
        return; // Ignore malformed frames rather than crashing the session.
      }
      if (this.messageHandlers.size === 0) {
        this.pending.push(message);
        return;
      }
      this.messageHandlers.forEach((handler) => handler(message));
    });

    this.ws.addEventListener("close", (event) => {
      if (this.closedByUs) return;
      this.closedHandlers.forEach((handler) => handler(event));
    });
  }

  async ready(): Promise<void> {
    return this.openPromise;
  }

  get isOpen(): boolean {
    return this.ws.readyState === WebSocket.OPEN;
  }

  onMessage(handler: (message: SignalMessage) => void): () => void {
    this.messageHandlers.add(handler);
    if (this.pending.length > 0) {
      const queued = this.pending;
      this.pending = [];
      queued.forEach((message) => handler(message));
    }
    return () => this.messageHandlers.delete(handler);
  }

  /** Fires only for a close we did not initiate — i.e. an actual drop. */
  onClose(handler: (event: CloseEvent) => void): () => void {
    this.closedHandlers.add(handler);
    return () => this.closedHandlers.delete(handler);
  }

  send(message: SignalMessage): void {
    if (this.ws.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(message));
  }

  close(): void {
    this.closedByUs = true;
    if (this.ws.readyState === WebSocket.OPEN) {
      this.send({ type: "bye", data: {} });
    }
    this.ws.close();
  }
}

export class SignalingError extends Error {
  constructor(
    message: string,
    readonly code?: number,
  ) {
    super(message);
    this.name = "SignalingError";
  }
}

/** Close codes the backend uses on the signaling endpoint. */
export const WS_TICKET_REJECTED = 4401;
export const WS_SESSION_NOT_FOUND = 4404;

export interface DeviceConnectionHandlers {
  iceServers: IceServer[];
  onTrack?: (stream: MediaStream) => void;
  onDataChannel?: (channel: RTCDataChannel) => void;
  onIceCandidate?: (candidate: RTCIceCandidateInit) => void;
  onConnectionStateChange?: (state: RTCPeerConnectionState) => void;
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
  pc.addEventListener("connectionstatechange", () => handlers.onConnectionStateChange?.(pc.connectionState));

  return pc;
}

/**
 * Holds ICE candidates that arrive before the remote description is set.
 *
 * The phone starts trickling candidates the moment it creates its offer, and
 * the relay replays whatever was queued as soon as we connect — so a
 * candidate routinely reaches us in the same burst as, or just ahead of, the
 * offer it belongs to. addIceCandidate() throws in that state, which used to
 * abort negotiation outright.
 */
export class IceCandidateQueue {
  private queued: RTCIceCandidateInit[] = [];
  private remoteReady = false;

  constructor(private readonly pc: RTCPeerConnection) {}

  async add(candidate: RTCIceCandidateInit): Promise<void> {
    if (!this.remoteReady) {
      this.queued.push(candidate);
      return;
    }
    await this.pc.addIceCandidate(candidate).catch(() => {
      // A candidate that no longer applies is not worth failing the session.
    });
  }

  /** Call once the remote description is in place; flushes anything held. */
  async remoteDescriptionSet(): Promise<void> {
    this.remoteReady = true;
    const queued = this.queued;
    this.queued = [];
    for (const candidate of queued) {
      await this.pc.addIceCandidate(candidate).catch(() => {});
    }
  }
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
