# IMPORT LIBRARIES
import hashlib
import os
import re
import dataclasses

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from services import auth, db

from core.llm import analyze_resume
from core.pdf_reader import inspect_pdf, has_readable_text
from core.rules import run_all_checks
from core.rewriter import rewrite_bullet
from core.exporter import build_docx
from core.schemas import ResumeData, Job, School

from core.scoring import compute_overall_score, requirements_score, score_band, readiness_score
from core.safety import looks_like_injection

MAX_FILE_SIZE_MB = 5  # Maximum file size in megabytes
MAX_CACHE_ENTRIES = 100  # Maximum number of entries to keep in the cache

import sentry_sdk

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Enable performance monitoring
        send_default_pii=False,
        include_local_variables=False,
    )

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
    """A dictionary that survives button clicks while the app is running. Each entry tracks access time."""
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

def show_history():
    st.subheader("🕑 Your Past Analyses")
    rows = db.list_analyses(sb)
    if not rows:
        st.info("No saved analyses yet. Run one and it will appear here.")
        return
    for row in rows:
        when = row["created_at"][:10]
        label = row["job_label"] or "Untitled job"
        with st.expander(f"{when} — {label} — score {row['overall_score']}/100"):
            result = row["result"]
            st.write("**Strengths**")
            for item in result.get("strengths", []):
                st.write(f"- {item}")
            st.write("**Top fixes**")
            for item in result.get("top_fixes", []):
                st.write(f"- {item}")
            if row.get("flags"):
                st.write("**Remote application flags**")
                for flag in row["flags"]:
                    st.write(f"- {flag['title']}")


def show_privacy():
    st.subheader("🔒 Privacy")
    st.write(
        "Optima does not store your resume or job description. After each analysis we save only "
        "the results (scores, suggestions and flags) so you can see your history. "
        "We also keep a simple count of how many analyses you've run this month."
    )
    st.write("You can delete your saved history at any time.")
    confirm = st.checkbox("I understand this permanently deletes my saved analyses")
    if st.button("Delete my history", disabled=not confirm):
        if db.delete_my_history(sb):
            st.success("Your saved history has been deleted.")
        else:
            st.error("Something went wrong. Please try again.")

BULLET_MARKERS = ("•", "●", "▪", "■", "◦", "·", "-", "–", "*")


def find_bullets(text):
    """Pulls likely bullet points out of resume text."""
    found = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(BULLET_MARKERS):
            line = line.lstrip("".join(BULLET_MARKERS) + " ")
            if 25 <= len(line) <= 400:
                found.append(line)
    return found


def show_rewriter():
    st.subheader("✍️ Bullet Rewriter")
    st.caption(
        "Turn a weak resume bullet into a stronger one. Optima never invents numbers: "
        "you fill in the [brackets] with your real figures."
    )

    plan = db.get_plan(sb)
    used = db.count_this_month(sb, kind="rewrite")
    if plan != "pro":
        if used is None:
            st.error("We couldn't check your usage right now. Please try again in a moment.")
            return
        st.caption(f"Free rewrites used this month: {used}/{db.FREE_REWRITES_PER_MONTH}")

    picked = ""
    upload = st.file_uploader("Optional: upload your resume to pick a bullet from it", type=["pdf"], key="rewrite_upload")
    if upload and upload.size <= MAX_FILE_SIZE_MB * 1024 * 1024:
        bullets = find_bullets(inspect_pdf(upload.getvalue()).text)
        if bullets:
            picked = st.selectbox("Pick a bullet", [""] + bullets)
        else:
            st.info("We couldn't find bullet points in that PDF. Paste one below instead.")

    bullet = st.text_area("Resume bullet", value=picked, max_chars=500, height=100)
    job_context = st.text_input("Target job title (optional)", max_chars=100)

    if st.button("Rewrite"):
        if len(bullet.strip()) < 15:
            st.warning("Please enter a longer bullet point.")
            return
        if plan != "pro" and used >= db.FREE_REWRITES_PER_MONTH:
            st.warning("You've used your free rewrites for this month. Paid plans are coming soon.")
            return

        with st.spinner("Rewriting..."):
            result = rewrite_bullet(client, bullet.strip(), job_context.strip())

        if result is None:
            st.error("We couldn't rewrite your bullet. This might be due to a network issue or the AI service being temporarily unavailable. Please try again in a moment. If the problem persists, contact support.")
            return

        db.record_usage(sb, kind="rewrite")

        st.markdown("### What's weak about the original")
        for item in result.problems:
            st.write(f"- {item}")

        st.markdown("### Stronger versions")
        st.caption("Replace anything in [square brackets] with your real numbers. Use the copy button on the right.")
        for r in result.rewrites:
            st.write(f"**{r.approach}**")
            st.code(r.text, language=None)

        st.markdown("### Questions to help you find your real numbers")
        for q in result.metric_questions:
            st.write(f"- {q}")

def show_export():
    st.subheader("📄 Build Your Resume")
    st.caption(
        "Fill in each section, then download an ATS-friendly resume: single column, standard headings, "
        "no photo or personal details that remote employers don't expect."
    )

    if db.get_plan(sb) != "pro":
        st.info("Resume export is a Pro feature. Paid plans are coming soon.")
        return

    st.markdown("#### Contact")
    full_name = st.text_input("Full name")
    headline = st.text_input("Headline (for example: Customer Support Specialist)")
    c1, c2 = st.columns(2)
    email = c1.text_input("Email")
    phone = c2.text_input("Phone (with country code, e.g. +234 801 234 5678)")
    location = c1.text_input("Location and time zone (e.g. Lagos, Nigeria, GMT+1)")
    linkedin = c2.text_input("LinkedIn address")

    st.markdown("#### Professional Summary")
    summary = st.text_area("2-3 lines: your role, years of experience, and your strongest result", height=100)

    st.markdown("#### Work Experience")
    job_count = st.number_input("How many jobs to include?", min_value=0, max_value=6, value=1, step=1)
    jobs = []
    for i in range(int(job_count)):
        with st.expander(f"Job {i + 1}", expanded=(i == 0)):
            title = st.text_input("Job title", key=f"job_title_{i}")
            company = st.text_input("Company", key=f"job_company_{i}")
            job_location = st.text_input("Location (optional)", key=f"job_loc_{i}")
            d1, d2 = st.columns(2)
            start = d1.text_input("Start (e.g. Jan 2022)", key=f"job_start_{i}")
            end = d2.text_input("End (e.g. Mar 2024 or Present)", key=f"job_end_{i}")
            bullets_text = st.text_area("Bullets (one per line)", key=f"job_bullets_{i}", height=140)
            if title and company:
                jobs.append(Job(
                    title=title.strip(), company=company.strip(), location=job_location.strip(),
                    start=start.strip(), end=end.strip(),
                    bullets=[b.strip() for b in bullets_text.splitlines() if b.strip()],
                ))

    st.markdown("#### Education")
    school_count = st.number_input("How many entries?", min_value=0, max_value=4, value=1, step=1)
    education = []
    for i in range(int(school_count)):
        with st.expander(f"Education {i + 1}", expanded=(i == 0)):
            qualification = st.text_input("Qualification (e.g. BSc Computer Science)", key=f"edu_q_{i}")
            institution = st.text_input("Institution", key=f"edu_i_{i}")
            year = st.text_input("Year (optional)", key=f"edu_y_{i}")
            if qualification and institution:
                education.append(School(
                    qualification=qualification.strip(), institution=institution.strip(), year=year.strip(),
                ))

    st.markdown("#### Skills")
    skills_text = st.text_area("Skills, separated by commas")

    if st.button("Create my resume"):
        if not full_name.strip() or not email.strip():
            st.warning("Please enter at least your name and email.")
            return

        data = ResumeData(
            full_name=full_name.strip(), headline=headline.strip(), email=email.strip(),
            phone=phone.strip(), location=location.strip(), linkedin=linkedin.strip(),
            summary=summary.strip(), jobs=jobs, education=education,
            skills=[s.strip() for s in skills_text.split(",") if s.strip()],
        )
        st.session_state["export_bytes"] = build_docx(data)

    if "export_bytes" in st.session_state:
        st.success("Your resume is ready.")
        st.download_button(
            "⬇️ Download as Word (.docx)",
            data=st.session_state["export_bytes"],
            file_name="resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.caption("To get a PDF, open the file in Word or Google Docs and choose Save as PDF.")

st.set_page_config(page_title="Optima", page_icon="🤖")
st.title("Optima")
user = auth.current_user()
if user is None:
    show_login_screen()
    st.stop()

sb = auth.get_client()
used_this_month = db.count_this_month(sb)

st.sidebar.write(f"Logged in as **{user.email}**")

page = st.sidebar.radio("Menu", ["Analyze", "Rewrite bullets","Build resume", "History", "Privacy"])

if used_this_month is not None:
    st.sidebar.caption(f"Free analyses used this month: {used_this_month}/{db.FREE_MONTHLY_LIMIT}")

if page == "Build resume":
    show_export()
    st.stop()

if page == "History":
    show_history()
    st.stop()
if page == "Privacy":
    show_privacy()
    st.stop()
if page == "Rewrite bullets":
    show_rewriter()
    st.stop()

if st.sidebar.button("Log out"):
    auth.sign_out()
    st.rerun()
st.write("**AI-Powered Resume Analyzer**")
st.write("Upload your resume and paste a job description. Let AI tell you how well you match!")

resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
jd_input = st.text_area("Paste the Job Description here", height=250, max_chars=8000)
job_label = st.text_input("Job title or company (optional, helps you find this later)", max_chars=100)

# RUN THE ANALYSIS
analyze_button = st.button("Analyze Match")
if analyze_button:
    if resume_file and jd_input:
        if resume_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"Your file is too large. Please upload a PDF smaller than {MAX_FILE_SIZE_MB} MB.")
            st.stop()

        if used_this_month is None:
            st.error("We couldn't check your usage right now. Please try again in a moment.")
            st.stop()
        if used_this_month >= db.FREE_MONTHLY_LIMIT:
            st.warning(f"You've used your {db.FREE_MONTHLY_LIMIT} free analyses for this month. Paid plans are coming soon.")
            st.stop()
        # Rate limit check
        rate_allowed, rate_message = db.check_rate_limit(sb)
        if not rate_allowed:
            st.warning(rate_message)
            st.stop()

        with st.spinner("Analyzing with AI..."):
            pdf_info = inspect_pdf(resume_file.getvalue())
            resume_text = pdf_info.text

            if not has_readable_text(resume_text):
                st.error("We couldn't read text from this PDF. Try exporting your resume as a text-based PDF from Word or Google Docs.")
                st.stop()

            flags = run_all_checks(pdf_info)

            if looks_like_injection(resume_text) or looks_like_injection(jd_input):
                st.warning("⚠️ Your resume or job description contains wording that looks like instructions to an AI. Optima treats everything you submit as plain content and will not follow it.")

            # Check cache before making API call
            cache = get_result_cache()
            resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
            jd_hash = hashlib.sha256(jd_input.encode()).hexdigest()
            key = hashlib.sha256(f"{resume_hash}||{jd_hash}".encode()).hexdigest()

            import time
            cached_entry = cache.get(key)

            if cached_entry is not None:
                # Update last accessed time
                cached_entry["last_accessed"] = time.time()
                result = cached_entry["result"]
            else:
                result = analyze_resume(client, resume_text, jd_input)
                if result is not None:
                    if len(cache) >= MAX_CACHE_ENTRIES:
                        # Remove the least recently used entry
                        oldest_key = min(cache.keys(), key=lambda k: cache[k]["last_accessed"])
                        cache.pop(oldest_key)
                    cache[key] = {"result": result, "last_accessed": time.time()}

        if result is None:
            st.error("We couldn't complete the analysis. This might be due to a network issue or the AI service being temporarily unavailable. Please try again in a moment. If the problem persists, contact support.")
        else:
            overall = compute_overall_score(result)

            db.record_usage(sb)
            db.save_analysis(
                sb,
                job_label.strip(),
                overall,
                result.model_dump(),
                [dataclasses.asdict(f) for f in flags],
            )

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