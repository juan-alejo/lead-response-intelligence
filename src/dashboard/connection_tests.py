"""Test-connection helpers for the Settings tab.

Each function attempts the **cheapest possible live call** against the
provider so the operator can verify their credentials in one click
without a full pipeline run.

All functions return a `(ok: bool, message: str)` tuple — the UI layer
renders ✅/❌ accordingly.

Keep these defensive: a failed test must never crash the app. Every
known exception type is caught and translated into a user-friendly
message.
"""

from __future__ import annotations


def test_anthropic(api_key: str, model: str = "claude-sonnet-4-6") -> tuple[bool, str]:
    if not api_key:
        return False, "API key vacía."
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        # Minimal message: 1 output token, costs ~$0.00001.
        client.messages.create(
            model=model,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, "Conexión OK."
    except Exception as e:  # noqa: BLE001
        return False, _humanize_error(e)


def test_google_places(api_key: str) -> tuple[bool, str]:
    if not api_key:
        return False, "API key vacía."
    try:
        import httpx

        resp = httpx.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": "pizza nyc", "key": api_key},
            timeout=10.0,
        )
        data = resp.json()
        status = data.get("status")
        if status == "OK" or status == "ZERO_RESULTS":
            return True, "Conexión OK."
        err = data.get("error_message") or status or "respuesta inesperada"
        return False, f"Google respondió: {err}"
    except Exception as e:  # noqa: BLE001
        return False, _humanize_error(e)


def test_airtable(api_key: str, base_id: str) -> tuple[bool, str]:
    if not api_key or not base_id:
        return False, "API key y/o Base ID vacíos."
    try:
        import httpx

        resp = httpx.get(
            f"https://api.airtable.com/v0/meta/bases/{base_id}/tables",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            tables = resp.json().get("tables") or []
            return True, f"OK — {len(tables)} tabla(s) en la base."
        is_json = resp.headers.get("content-type", "").startswith("application/json")
        err = resp.json().get("error") if is_json else resp.text
        return False, f"Airtable HTTP {resp.status_code}: {err}"
    except Exception as e:  # noqa: BLE001
        return False, _humanize_error(e)


def test_twilio(account_sid: str, auth_token: str) -> tuple[bool, str]:
    if not account_sid or not auth_token:
        return False, "Account SID y/o Auth Token vacíos."
    try:
        import httpx

        resp = httpx.get(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json",
            auth=(account_sid, auth_token),
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, f"OK — cuenta: {data.get('friendly_name', 'sin nombre')}"
        return False, f"Twilio HTTP {resp.status_code}: {resp.text[:140]}"
    except Exception as e:  # noqa: BLE001
        return False, _humanize_error(e)


def _humanize_error(exc: Exception) -> str:
    """Shrink ugly traceback text to something readable in a toast."""
    msg = str(exc)
    if len(msg) > 180:
        msg = msg[:180] + "…"
    return msg or type(exc).__name__
