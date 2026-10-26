# IMPORT LIBRARIES
import hashlib
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from services import auth

from core.llm import analyze_resume
from core.pdf_reader import inspect_pdf, has_readable_text
from core.rules import run_all_checks

from core.scoring import compute_overall_score, requirements_score, score_band, readiness_score
from core.safety import looks_like_injection

MAX_FILE_SIZE_MB = 5  # Maximum file size in megabytes
MAX_CACHE_ENTRIES = 100  # Maximum number of entries to keep in the cache

# LOAD API KEY
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, AttributeError):
        api_key = None

if not api_key:
    st.error("❌ OpenAI API key not found! Please set it in `.env` locally or Streamlit Secrets on cloud.")
    st.stop()

client = OpenAI(api_key=api_key, timeout=60)
@st.cache_resource
def get_result_cache():
    """A dictionary that survives button clicks while the app is running."""
    return {}

# BUILD THE WEB INTERFACE WITH STREAMLIT
def show_login_screen():
    st.write("Log in or create a free account to analyze your resume.")
    login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
        if submitted:
            ok, message = auth.sign_in(email.strip(), password)
            if ok:
                st.rerun()
            else:
                st.error(message)

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Choose a password (8+ characters)", type="password", key="signup_password")
            created = st.form_submit_button("Create account")
        if created:
            ok, message = auth.sign_up(new_email.strip(), new_password)
            if ok:
                st.success(message)
                if auth.current_user() is not None:
                    st.rerun()
            else:
                st.error(message)
SEVERITY_ORDER = ["high", "medium", "low"]
SEVERITY_ICON = {"high": "🔴", "medium": "🟠", "low": "🟢"}


def show_flags(flags):
    st.subheader("🌍 Remote Application Check")
    st.caption("These checks use fixed rules, not AI, so the same CV always gets the same results.")

    if not flags:
        st.success("No common problems found. Your CV looks ready for remote applications.")
        return

    score = readiness_score(flags)
    st.metric("Application Readiness", f"{score}/100")
    st.progress(score / 100)

    for flag in sorted(flags, key=lambda f: SEVERITY_ORDER.index(f.severity)):
        with st.expander(f"{SEVERITY_ICON[flag.severity]} {flag.title}"):
            st.write(f"**Why it matters:** {flag.why}")
            st.write(f"**What to do:** {flag.fix}")
st.set_page_config(page_title="Optima", page_icon="🤖")
st.title("Optima")
user = auth.current_user()
if user is None:
    show_login_screen()
    st.stop()

st.sidebar.write(f"Logged in as **{user.email}**")
if st.sidebar.button("Log out"):
    auth.sign_out()
    st.rerun()
st.write("**AI-Powered Resume Analyzer**")
st.write("Upload your resume and paste a job description. Let AI tell you how well you match!")

resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
jd_input = st.text_area("Paste the Job Description here", height=250, max_chars=8000)

# RUN THE ANALYSIS
analyze_button = st.button("Analyze Match")
if analyze_button:
    if resume_file and jd_input:
        if resume_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"Your file is too large. Please upload a PDF smaller than {MAX_FILE_SIZE_MB} MB.")
            st.stop()

        with st.spinner("Analyzing with AI..."):
            pdf_info = inspect_pdf(resume_file.getvalue())
            resume_text = pdf_info.text

            if not has_readable_text(resume_text):
                st.error("We couldn't read text from this PDF. Try exporting your resume as a text-based PDF from Word or Google Docs.")
                st.stop()

            flags = run_all_checks(pdf_info)
            result = analyze_resume(client, resume_text, jd_input)                        
            
            if looks_like_injection(resume_text) or looks_like_injection(jd_input):
                st.warning("⚠️ Your resume or job description contains wording that looks like instructions to an AI. Optima treats everything you submit as plain content and will not follow it.")
            
            cache = get_result_cache()
            resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
            jd_hash = hashlib.sha256(jd_input.encode()).hexdigest()
            key = hashlib.sha256(f"{resume_hash}||{jd_hash}".encode()).hexdigest()

            result = cache.get(key)

            if result is None:
                result = analyze_resume(client, resume_text, jd_input)
                if result is not None:
                    if len(cache) >= MAX_CACHE_ENTRIES:
                        # Remove the oldest entry in the cache
                        oldest_key = next(iter(cache))
                        cache.pop(oldest_key)
                    cache[key] = result

        if result is None:
            st.error("Something went wrong while analyzing your resume. Please try again in a moment.")
        else:
            overall = compute_overall_score(result)

            st.subheader("📋 Your Results")
            st.metric("Overall Match", f"{overall}/100")
            st.progress(overall / 100)
            st.caption(score_band(overall))

            c1, c2, c3 = st.columns(3)
            c1.metric("Requirements met", f"{requirements_score(result)}%")
            c2.metric("Experience fit", f"{result.experience_level}/5")
            c3.metric("Achievements", f"{result.achievements_level}/5")

            st.markdown("### ✅ Strengths")
            for item in result.strengths:
                st.write(f"- {item}")

            missing = [r for r in result.requirements if not r.found]
            st.markdown("### 🔑 Missing Requirements")
            if not missing:
                st.write("Every requirement was found in your resume.")
            order = ["high", "medium", "low"]
            icons = {"high": "🔴", "medium": "🟠", "low": "🟢"}
            for r in sorted(missing, key=lambda r: order.index(r.importance)):
                with st.expander(f"{icons[r.importance]} {r.name} ({r.importance} priority)"):
                    st.write(f"**What to do:** {r.suggestion}")

            with st.expander("See the full checklist"):
                for r in result.requirements:
                    mark = "✅" if r.found else "❌"
                    st.write(f"{mark} **{r.name}** ({r.importance})" + (f": {r.evidence}" if r.evidence else ""))

            st.markdown("### 🛠 Top Fixes")
            for item in result.top_fixes:
                st.write(f"- {item}")
                
        show_flags(flags)
    else:
        st.warning("Please upload a resume and enter a job description.")