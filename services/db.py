import logging

logger = logging.getLogger(__name__)

from datetime import datetime, timezone

FREE_MONTHLY_LIMIT = 20
FREE_REWRITES_PER_MONTH = 30


def _month_start():
    """The start of the current month (UTC), as text Supabase understands."""
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def count_this_month(sb, kind="analysis"):
    """How many uses of this kind this month. Returns None if we couldn't check."""
    try:
        response = (
            sb.table("usage")
            .select("id", count="exact")
            .eq("kind", kind)
            .gte("created_at", _month_start())
            .execute()
        )
        return response.count or 0
    except Exception as e:
        logger.error(f"Usage check failed: {type(e).__name__}: {e}")
        return None


def record_usage(sb, kind="analysis"):
    """Adds one use of this kind for the user."""
    try:
        sb.table("usage").insert({"kind": kind}).execute()
    except Exception as e:
        logger.error(f"Recording usage failed: {type(e).__name__}: {e}")

def get_plan(sb):
    """Returns 'free' or 'pro'. If anything goes wrong, treats the user as free."""
    try:
        response = sb.table("profiles").select("plan").limit(1).execute()
        if response.data:
            return response.data[0]["plan"]
    except Exception as e:
        logger.error(f"Plan check failed: {type(e).__name__}: {e}")
    return "free"


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
        logger.error(f"Saving analysis failed: {type(e).__name__}: {e}")
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
        logger.error(f"Loading history failed: {type(e).__name__}: {e}")
        return []


def delete_my_history(sb):
    """Deletes all of this user's saved analyses. Returns True if it worked."""
    try:
        sb.table("analyses").delete().gte("created_at", "1970-01-01T00:00:00Z").execute()
        return True
    except Exception as e:
        logger.error(f"Deleting history failed: {type(e).__name__}: {e}")
        return False

def check_rate_limit(sb, max_calls_per_minute=10):
    """Checks if user has exceeded rate limit. Returns (allowed, message)."""
    try:
        # Get calls in the last minute
        one_minute_ago = datetime.now(timezone.utc).replace(second=0, microsecond=0) - __import__('datetime').timedelta(minutes=1)
        response = (
            sb.table("usage")
            .select("id", count="exact")
            .gte("created_at", one_minute_ago.isoformat())
            .execute()
        )
        count = response.count or 0
        if count >= max_calls_per_minute:
            return False, f"You've made {count} calls in the last minute. Please wait a moment."
        return True, ""
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True, ""  # Allow on error to not block legitimate users