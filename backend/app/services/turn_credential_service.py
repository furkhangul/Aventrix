import base64
import hashlib
import hmac
import time
import uuid

from app.core.config import get_settings
from app.schemas.device import IceServer

settings = get_settings()

# coturn's REST API time-limited credential scheme: username is
# "<unix-expiry>:<label>", credential is base64(HMAC-SHA1(shared_secret, username)).
# See https://github.com/coturn/coturn/blob/master/docs/turn-rest-api.md
CREDENTIAL_TTL_SECONDS = 3600


def _generate_turn_credential(label: str) -> tuple[str, str]:
    expiry = int(time.time()) + CREDENTIAL_TTL_SECONDS
    username = f"{expiry}:{label}"
    secret = (settings.turn_shared_secret or "").encode()
    digest = hmac.new(secret, username.encode(), hashlib.sha1).digest()
    credential = base64.b64encode(digest).decode()
    return username, credential


def generate_ice_servers(*, subject_id: uuid.UUID) -> list[IceServer]:
    """
    Builds the RTCConfiguration.iceServers list handed to both peers of a
    session: a public/self-hosted STUN entry plus a coturn TURN entry with
    a fresh, time-limited credential scoped to this subject. If no TURN
    shared secret is configured, only STUN is returned — same-network
    (same-LAN or same-machine loopback) peers can still connect via STUN
    alone; only NAT-crossing relay needs TURN.
    """
    servers = [IceServer(urls=settings.stun_server_url)]
    if settings.turn_shared_secret:
        username, credential = _generate_turn_credential(str(subject_id))
        servers.append(IceServer(urls=settings.turn_server_url, username=username, credential=credential))
    return servers
