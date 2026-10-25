import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

MIN_PASSWORD_LENGTH = 8


def _get_setting(name):
    """Reads a setting from .env locally, or from Streamlit Secrets on the cloud."""
    value = os.getenv(name)
    if not value:
        try:
            value = st.secrets[name]
        except Exception:
            value = None
    return value


def _get_client():
    """Returns this visitor's own Supabase connection, creating it the first time."""
    if "supabase_client" not in st.session_state:
        url = _get_setting("SUPABASE_URL")
        key = _get_setting("SUPABASE_ANON_KEY")
        if not url or not key:
            return None
        st.session_state["supabase_client"] = create_client(url, key)
    return st.session_state["supabase_client"]


def current_user():
    """Returns the logged-in user, or None if nobody is logged in."""
    return st.session_state.get("user")


def sign_up(email, password):
    """Creates an account. Returns (success, message to show the user)."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Your password must be at least {MIN_PASSWORD_LENGTH} characters."

    client = _get_client()
    if client is None:
        return False, "Login is not set up yet. Please try again later."

    try:
        response = client.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        print(f"Sign-up error: {type(e).__name__}: {e}")
        return False, "We couldn't create your account. Check your email address and try again."

    if response.session is None:
        return True, "Account created! Check your email, click the confirmation link, then log in."

    st.session_state["user"] = response.user  # confirmation is switched off, so they're in
    return True, "Account created. You are logged in."


def sign_in(email, password):
    """Logs a user in. Returns (success, message to show the user)."""
    client = _get_client()
    if client is None:
        return False, "Login is not set up yet. Please try again later."

    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        print(f"Sign-in error: {type(e).__name__}: {e}")
        return False, "Incorrect email or password, or your email isn't confirmed yet."

    st.session_state["user"] = response.user
    return True, ""


def sign_out():
    """Logs the user out and forgets their connection."""
    client = st.session_state.get("supabase_client")
    if client is not None:
        try:
            client.auth.sign_out()
        except Exception as e:
            print(f"Sign-out error: {e}")
    st.session_state.pop("user", None)
    st.session_state.pop("supabase_client", None)