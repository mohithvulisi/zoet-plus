from __future__ import annotations

from .config import get_setting


def _split_urls(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def get_rtc_configuration() -> dict:
    stun_urls = _split_urls(get_setting("STUN_URLS", "stun:stun.l.google.com:19302"))
    ice_servers: list[dict] = []
    if stun_urls:
        ice_servers.append({"urls": stun_urls})

    turn_urls = _split_urls(get_setting("TURN_URL", ""))
    turn_username = get_setting("TURN_USERNAME", "")
    turn_credential = get_setting("TURN_CREDENTIAL", "")
    if turn_urls and turn_username and turn_credential:
        ice_servers.append(
            {
                "urls": turn_urls,
                "username": turn_username,
                "credential": turn_credential,
            }
        )

    return {"iceServers": ice_servers}
