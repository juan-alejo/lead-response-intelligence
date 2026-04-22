"""Optional password protection for public deployments.

Activated only when `DASHBOARD_PASSWORD` is set in the environment. When
unset, the dashboard is open — fine for local dev / internal use behind
a VPN. When set, the dashboard shows a minimal login form on first load
and persists the authenticated state in `st.session_state` for the rest
of the session.

This is intentionally simple — a single shared password, not multi-user
auth. For a SaaS deployment with per-user accounts you'd wire in a real
auth provider (Clerk, Auth0, Supabase Auth).
"""

from __future__ import annotations

import hmac
import os

import streamlit as st


def _password_configured() -> str | None:
    password = os.environ.get("DASHBOARD_PASSWORD", "").strip()
    return password or None


def require_auth() -> None:
    """Short-circuit the app with a login form when a password is configured.

    Call this BEFORE rendering any dashboard content. If the operator hasn't
    authenticated yet, shows a login prompt and `st.stop()`s the script.
    """
    expected = _password_configured()
    if expected is None:
        return  # open deployment — no auth required

    if st.session_state.get("_authed"):
        return  # already authenticated this session

    st.markdown("# 🔒 ReachRate")
    st.caption(
        "Este panel está protegido. Ingresá la contraseña que te compartió "
        "el administrador."
    )
    with st.form("auth_form"):
        pwd = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", type="primary")

    if submitted:
        # Use hmac.compare_digest to avoid a timing attack on the password check.
        if hmac.compare_digest(pwd, expected):
            st.session_state["_authed"] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta.")

    st.stop()
