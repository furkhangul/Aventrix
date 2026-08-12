from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Best-effort client IP resolution. X-Forwarded-For is only trusted because
    nginx (the only thing allowed to sit in front of this service) always
    sets it — never trust this header if the app were exposed directly.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
