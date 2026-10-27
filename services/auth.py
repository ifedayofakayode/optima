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


def get_client():
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

    client = get_client()
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
    client = get_client()
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

from datetime import datetime, timezone

FREE_MONTHLY_LIMIT = 2


def _month_start():
    """The start of the current month (UTC), as text Supabase understands."""
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def count_this_month(sb):
    """How many analyses this user has run this month. Returns None if we couldn't check."""
    try:
        response = (
            sb.table("usage")
            .select("id", count="exact")
            .gte("created_at", _month_start())
            .execute()
        )
        return response.count or 0
    except Exception as e:
        print(f"Usage check failed: {type(e).__name__}: {e}")
        return None


def record_usage(sb):
    """Adds one to this user's count for the month."""
    try:
        sb.table("usage").insert({}).execute()
    except Exception as e:
        print(f"Recording usage failed: {type(e).__name__}: {e}")


def save_analysis(sb, job_label, overall_score, result_dict, flags_list):
    """Saves the results of one analysis. Returns True if it worked."""
    try:
        sb.table("analyses").insert({
            "job_label": job_label or None,
            "overall_score": overall_score,
            "result": result_dict,
            "flags": flags_list,
        }).execute()
        return True
    except Exception as e:
        print(f"Saving analysis failed: {type(e).__name__}: {e}")
        return False


def list_analyses(sb, limit=20):
    """The user's most recent analyses, newest first."""
    try:
        response = (
            sb.table("analyses")
            .select("id, job_label, overall_score, created_at, result, flags")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Loading history failed: {type(e).__name__}: {e}")
        return []


def delete_my_history(sb):
    """Deletes all of this user's saved analyses. Returns True if it worked."""
    try:
        sb.table("analyses").delete().gte("created_at", "1970-01-01").execute()
        return True
    except Exception as e:
        print(f"Deleting history failed: {type(e).__name__}: {e}")
        return False