# IMPORT LIBRARIES
import hashlib
import os
import re
import dataclasses

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from services import auth, db

from core.llm import analyze_resume, parse_resume, generate_resume, generate_cover_letter
from core.pdf_reader import inspect_pdf, has_readable_text, read_docx
from core.rules import run_all_checks
from core.rewriter import rewrite_bullet
from core.exporter import build_docx, build_cover_letter_docx, build_pdf
from core.schemas import ResumeData, Job, School, ConfirmableItem, ParsedResume, CoverLetter
from core.confirmation import extract_confirmable_items, build_confirmed_gap_data

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


def show_gap_confirmation(confirmable_items: list) -> list:
    """Present missing requirements for user confirmation."""
    st.subheader("🔍 Confirm Your Skills & Experience")
    st.caption(
        "The job description asks for these items, but we didn't find them in your resume. "
        "Please confirm which ones you genuinely have. Only confirmed items will be added to your tailored resume."
    )

    # Initialize session state for confirmations if not exists
    if "confirmations" not in st.session_state:
        st.session_state["confirmations"] = {}

    # Sort by importance
    importance_order = {"high": 0, "medium": 1, "low": 2}
    sorted_items = sorted(confirmable_items, key=lambda x: importance_order[x.importance])

    updated_items = []

    for i, item in enumerate(sorted_items):
        icon = {"high": "🔴", "medium": "🟠", "low": "🟢"}[item.importance]
        item_key = f"item_{i}"

        # Get saved response from session state, or use default
        saved_response = st.session_state["confirmations"].get(item_key, {}).get("response", "unanswered")
        saved_evidence = st.session_state["confirmations"].get(item_key, {}).get("evidence", "")

        with st.expander(f"{icon} {item.name} ({item.importance} priority)", expanded=(i == 0)):
            st.write(f"**From job description:** {item.jd_source}")
            st.write(f"**Category:** {item.category}")
            st.write(f"**Suggestion:** {item.suggestion}")

            # Response options - default to saved value
            response = st.radio(
                "Do you have this?",
                options=["Yes", "Partially", "No"],
                key=f"response_{i}",
                horizontal=True,
                index=["Yes", "Partially", "No"].index(saved_response.capitalize()) if saved_response in ["yes", "partially", "no"] else 0
            )

            evidence = ""
            if response in ["Yes", "Partially"]:
                # Default to saved evidence
                evidence = st.text_area(
                    "Briefly describe your experience (years, context, a project)",
                    key=f"evidence_{i}",
                    height=80,
                    value=saved_evidence,
                    help="For example: '2 years using React at my current job' or 'Built 3 personal projects with Python'"
                )

            # Save to session state
            st.session_state["confirmations"][item_key] = {
                "response": response.lower(),
                "evidence": evidence,
            }

            # Update the item
            item.response = response.lower()
            item.evidence = evidence
            item.is_confirmed = response in ["yes", "partially"]

            updated_items.append(item)

    return updated_items


def show_honesty_summary(original_requirements: list, confirmed_items: list) -> str:
    """Generate and display an honesty summary."""
    # Only show summary if we have user interactions
    if "confirmations" not in st.session_state or not st.session_state["confirmations"]:
        return ""

    st.subheader("✅ Honesty Summary")

    # Count categories
    found_count = sum(1 for r in original_requirements if r.found)
    confirmed_count = sum(1 for i in confirmed_items if i.is_confirmed)
    excluded_count = sum(1 for i in confirmed_items if not i.is_confirmed)

    st.write(f"**From your original resume:** {found_count} requirements found")
    st.write(f"**Added from your confirmations:** {confirmed_count} items")
    st.write(f"**Excluded (honest gaps):** {excluded_count} items")

    if confirmed_count > 0:
        st.write("\n**Items being added to your resume:**")
        for item in confirmed_items:
            if item.is_confirmed:
                evidence_text = f" (evidence: {item.evidence})" if item.evidence else ""
                st.write(f"- {item.name}{evidence_text}")

    if excluded_count > 0:
        st.write("\n**Items excluded (gaps):**")
        for item in confirmed_items:
            if not item.is_confirmed:
                st.write(f"- {item.name}")

    st.warning(
        "⚠️ Only include what you can speak to confidently in an interview. "
        "If you over-claim, you may fail interviews and damage your reputation."
    )

    return f"Found: {found_count}, Confirmed: {confirmed_count}, Excluded: {excluded_count}"

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


def show_generated_resume(resume_data: ResumeData):
    """Display the generated resume with inline editing."""
    st.subheader("📄 Your Tailored Resume")
    st.caption("Review and edit your resume before downloading. Only change what's necessary.")

    # Contact info
    st.markdown("#### Contact Information")
    c1, c2, c3, c4 = st.columns(4)
    full_name = c1.text_input("Full Name", value=resume_data.full_name, key="gen_full_name")
    email = c2.text_input("Email", value=resume_data.email, key="gen_email")
    phone = c3.text_input("Phone", value=resume_data.phone, key="gen_phone")
    location = c4.text_input("Location", value=resume_data.location, key="gen_location")

    linkedin = st.text_input("LinkedIn", value=resume_data.linkedin, key="gen_linkedin")

    # Summary
    st.markdown("#### Professional Summary")
    summary = st.text_area("Summary", value=resume_data.summary, height=100, key="gen_summary")

    # Jobs
    st.markdown("#### Work Experience")
    jobs = []
    for i, job in enumerate(resume_data.jobs):
        with st.expander(f"{job.title} at {job.company}", expanded=(i == 0)):
            title = st.text_input("Job Title", value=job.title, key=f"gen_job_title_{i}")
            company = st.text_input("Company", value=job.company, key=f"gen_job_company_{i}")
            job_loc = st.text_input("Location", value=job.location, key=f"gen_job_loc_{i}")
            d1, d2 = st.columns(2)
            start = d1.text_input("Start Date", value=job.start, key=f"gen_job_start_{i}")
            end = d2.text_input("End Date", value=job.end, key=f"gen_job_end_{i}")

            bullets_text = st.text_area(
                "Bullet Points (one per line)",
                value="\n".join(job.bullets),
                height=150,
                key=f"gen_job_bullets_{i}"
            )

            if title and company:
                jobs.append(Job(
                    title=title.strip(),
                    company=company.strip(),
                    location=job_loc.strip(),
                    start=start.strip(),
                    end=end.strip(),
                    bullets=[b.strip() for b in bullets_text.splitlines() if b.strip()],
                ))

    # Education
    st.markdown("#### Education")
    education = []
    for i, school in enumerate(resume_data.education):
        with st.expander(f"{school.qualification}", expanded=(i == 0)):
            qualification = st.text_input("Qualification", value=school.qualification, key=f"gen_edu_q_{i}")
            institution = st.text_input("Institution", value=school.institution, key=f"gen_edu_i_{i}")
            year = st.text_input("Year", value=school.year, key=f"gen_edu_y_{i}")

            if qualification and institution:
                education.append(School(
                    qualification=qualification.strip(),
                    institution=institution.strip(),
                    year=year.strip(),
                ))

    # Skills
    st.markdown("#### Skills")
    skills_text = st.text_area(
        "Skills (comma-separated)",
        value=", ".join(resume_data.skills),
        key="gen_skills"
    )
    skills = [s.strip() for s in skills_text.split(",") if s.strip()]

    # Create updated ResumeData
    updated_resume = ResumeData(
        full_name=full_name.strip(),
        headline=resume_data.headline,
        email=email.strip(),
        phone=phone.strip(),
        location=location.strip(),
        linkedin=linkedin.strip(),
        summary=summary.strip(),
        jobs=jobs,
        education=education,
        skills=skills,
    )

    st.markdown("---")

    # Export buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Download as Word (.docx)", key="download_gen_resume"):
            docx_bytes = build_docx(updated_resume)
            st.download_button(
                "⬇️ Download Resume",
                data=docx_bytes,
                file_name=f"{updated_resume.full_name.replace(' ', '_')}_Resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    with col2:
        if st.button("Download as PDF", key="download_gen_resume_pdf"):
            pdf_bytes = build_pdf(updated_resume)
            st.download_button(
                "⬇️ Download Resume",
                data=pdf_bytes,
                file_name=f"{updated_resume.full_name.replace(' ', '_')}_Resume.pdf",
                mime="application/pdf",
            )

    with col3:
        st.success("✅ Both formats are ATS-friendly with selectable text.")

    return updated_resume


def show_cover_letter_generator():
    """Display cover letter generation UI and the generated cover letter."""
    st.subheader("✉️ Cover Letter Generator")
    st.caption(
        "Generate a tailored cover letter based on your resume, the job description, "
        "and your confirmed skills. Non-generic and evidence-based."
    )

    # Optional inputs
    st.markdown("#### Optional Customization")
    col1, col2 = st.columns(2)
    tone = col1.selectbox(
        "Tone",
        options=["professional", "warm", "confident"],
        index=0,
        help="Choose the tone that fits your style and the company culture."
    )
    hiring_manager = col2.text_input(
        "Hiring manager name (optional)",
        max_chars=100,
        help="If you know the hiring manager's name, include it for a personalized greeting."
    )

    why_company = st.text_area(
        "Why this company? (optional)",
        max_chars=500,
        height=80,
        help="Briefly explain why you're interested in this specific company (e.g., their mission, product, culture)."
    )

    # Generate button
    if st.button("🚀 Generate Cover Letter", key="generate_cover_letter_btn"):
        if "parsed_resume" not in st.session_state:
            st.error("Please generate a resume first before creating a cover letter.")
            return

        with st.spinner("Generating your cover letter..."):
            parsed_resume = st.session_state["parsed_resume"]
            jd_text = st.session_state["jd_text"]
            confirmed_items = st.session_state.get("confirmed_items", [])

            cover_letter = generate_cover_letter(
                client,
                parsed_resume,
                jd_text,
                confirmed_items,
                tone,
                hiring_manager,
                why_company
            )

            if cover_letter is None:
                st.error("We couldn't generate your cover letter. Please try again.")
            else:
                st.session_state["cover_letter"] = cover_letter
                st.success("Your cover letter is ready!")
                st.rerun()

    # Show generated cover letter if it exists
    if "cover_letter" in st.session_state:
        cover_letter = st.session_state["cover_letter"]

        st.markdown("---")
        st.subheader("📄 Your Cover Letter")

        # Display full text for easy reading
        st.markdown("#### Full Text")
        full_text = st.text_area(
            "Cover Letter",
            value=cover_letter.full_text,
            height=400,
            key="cover_letter_full_text"
        )

        # Word count
        word_count = len(full_text.split())
        st.caption(f"Word count: {word_count} (target: 250-350)")

        # Individual sections for fine-tuning
        with st.expander("Edit Individual Sections"):
            st.markdown("#### Structure")

            greeting = st.text_input("Greeting", value=cover_letter.greeting, key="cl_greeting")
            hook = st.text_area("Hook (opening)", value=cover_letter.hook, height=80, key="cl_hook")
            body1 = st.text_area("Body Paragraph 1", value=cover_letter.body_paragraph_1, height=120, key="cl_body1")
            body2 = st.text_area("Body Paragraph 2", value=cover_letter.body_paragraph_2, height=120, key="cl_body2")
            closing = st.text_area("Closing", value=cover_letter.closing, height=80, key="cl_closing")
            sign_off = st.text_input("Sign-off", value=cover_letter.sign_off, key="cl_sign_off")

            # Update cover letter with edits
            if st.button("Update Cover Letter", key="update_cl"):
                updated_cl = CoverLetter(
                    recipient_name=cover_letter.recipient_name,
                    company_name=cover_letter.company_name,
                    job_title=cover_letter.job_title,
                    greeting=greeting,
                    hook=hook,
                    body_paragraph_1=body1,
                    body_paragraph_2=body2,
                    closing=closing,
                    sign_off=sign_off,
                    full_text=full_text,
                )
                st.session_state["cover_letter"] = updated_cl
                st.success("Cover letter updated!")
                st.rerun()

        # Export
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download Cover Letter as Word (.docx)", key="download_cl"):
                docx_bytes = build_cover_letter_docx(cover_letter)
                st.download_button(
                    "⬇️ Download Cover Letter",
                    data=docx_bytes,
                    file_name=f"{cover_letter.company_name}_Cover_Letter.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

        with col2:
            st.info("💡 To get a PDF, download the Word file and save as PDF in Word or Google Docs.")


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

# Check if we have an analysis result in session state
has_analysis = "analysis_result" in st.session_state

st.write("**AI-Powered Resume Analyzer**")
st.write("Upload your resume and paste a job description. Let AI tell you how well you match!")

resume_file = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=["pdf", "docx"])
jd_input = st.text_area("Paste the Job Description here", height=250, max_chars=8000)
job_label = st.text_input("Job title or company (optional, helps you find this later)", max_chars=100)

# RUN THE ANALYSIS
analyze_button = st.button("Analyze Match")

# If we have analysis in session state, show results immediately
if has_analysis:
    result = st.session_state["analysis_result"]
    flags = st.session_state.get("flags", [])
    overall = st.session_state.get("overall_score", 0)

    st.subheader("📋 Your Results")
    st.metric("Overall Match", f"{overall}/100")
    st.progress(overall / 100)
    st.caption(score_band(overall))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Requirements met", f"{requirements_score(result)}%")
    c2.metric("ATS Score", f"{result.ats_score}/100")
    c3.metric("Experience fit", f"{result.experience_level}/5")
    c4.metric("Achievements", f"{result.achievements_level}/5")

    st.markdown("### ✅ Strengths")
    for item in result.strengths:
        st.write(f"- {item}")

    # Get confirmable items from session state or extract from result
    if "confirmable_items" in st.session_state:
        confirmable_items = st.session_state["confirmable_items"]
    else:
        confirmable_items = extract_confirmable_items(result)
        st.session_state["confirmable_items"] = confirmable_items

    # Show missing requirements summary
    missing = [r for r in result.requirements if not r.found]
    st.markdown("### 🔑 Missing Requirements")
    if not missing:
        st.write("Every requirement was found in your resume.")
    else:
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

    # ATS-specific sections
    if result.ats_score_explanation:
        st.markdown("### 📊 ATS Score Explanation")
        st.write(result.ats_score_explanation)

    if result.must_have_keywords:
        st.markdown("### 🔴 Must-Have Keywords (Missing)")
        for kw in result.must_have_keywords:
            st.write(f"- {kw}")

    if result.nice_to_have_keywords:
        st.markdown("### 🟡 Nice-to-Have Keywords (Missing)")
        for kw in result.nice_to_have_keywords:
            st.write(f"- {kw}")

    if result.critical_gaps:
        st.markdown("### ⚠️ Critical Gaps")
        for gap in result.critical_gaps:
            st.write(f"- {gap}")

    if result.ats_format_issues:
        st.markdown("### 📋 ATS Format Issues")
        for issue in result.ats_format_issues:
            st.write(f"- {issue}")

    # Show gap confirmation flow if there are missing items
    if confirmable_items:
        st.markdown("---")
        confirmed_items = show_gap_confirmation(confirmable_items)

        # Show honesty summary
        if confirmed_items:
            honesty_summary = show_honesty_summary(result.requirements, confirmed_items)

            # Store for generation
            st.session_state["confirmed_items"] = confirmed_items
            st.session_state["honesty_summary"] = honesty_summary

            # Show generate button
            st.markdown("---")
            if st.button("🚀 Generate Tailored Resume", key="generate_resume_btn"):
                with st.spinner("Parsing your resume and generating tailored version..."):
                    # Parse the resume
                    parsed_resume = parse_resume(client, st.session_state["resume_text"])

                    if parsed_resume is None:
                        st.error("We couldn't parse your resume. Please try again.")
                    else:
                        # Generate tailored resume
                        confirmed_items_list = st.session_state["confirmed_items"]
                        generated_resume = generate_resume(
                            client,
                            parsed_resume,
                            st.session_state["jd_text"],
                            confirmed_items_list
                        )

                        if generated_resume is None:
                            st.error("We couldn't generate your resume. Please try again.")
                        else:
                            # Store in session state
                            st.session_state["generated_resume"] = generated_resume
                            st.session_state["parsed_resume"] = parsed_resume
                            st.success("Your tailored resume is ready!")
                            st.rerun()
    else:
        st.success("No missing requirements to confirm - your resume covers all the key requirements!")

        # Still allow generation even if no gaps
        st.markdown("---")
        if st.button("🚀 Generate Tailored Resume", key="generate_resume_btn_no_gaps"):
            with st.spinner("Parsing your resume and generating tailored version..."):
                # Parse the resume
                parsed_resume = parse_resume(client, st.session_state["resume_text"])

                if parsed_resume is None:
                    st.error("We couldn't parse your resume. Please try again.")
                else:
                    # Generate tailored resume with no confirmed items
                    generated_resume = generate_resume(
                        client,
                        parsed_resume,
                        st.session_state["jd_text"],
                        []
                    )

                    if generated_resume is None:
                        st.error("We couldn't generate your resume. Please try again.")
                    else:
                        # Store in session state
                        st.session_state["generated_resume"] = generated_resume
                        st.session_state["parsed_resume"] = parsed_resume
                        st.success("Your tailored resume is ready!")
                        st.rerun()

    # Show generated resume if it exists
    if "generated_resume" in st.session_state:
        st.markdown("---")
        show_generated_resume(st.session_state["generated_resume"])

        # Show cover letter generation option
        st.markdown("---")
        st.subheader("✉️ Next: Generate Your Cover Letter")
        st.caption("Create a tailored cover letter to accompany your resume.")
        if st.button("📝 Generate Cover Letter", key="goto_cover_letter"):
            st.session_state["show_cover_letter"] = True
            st.rerun()

    # Show cover letter generator if triggered
    if st.session_state.get("show_cover_letter", False):
        st.markdown("---")
        show_cover_letter_generator()

    show_flags(flags)

    # Add button to start a new analysis
    st.markdown("---")
    if st.button("Start New Analysis"):
        # Clear analysis-related session state
        for key in ["analysis_result", "confirmable_items", "confirmed_items", "honesty_summary", "overall_score", "flags", "resume_text", "jd_text", "confirmations", "generated_resume", "parsed_resume", "cover_letter", "show_cover_letter"]:
            st.session_state.pop(key, None)
        st.rerun()

elif analyze_button:
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
            # Handle both PDF and DOCX
            if resume_file.type == "application/pdf":
                pdf_info = inspect_pdf(resume_file.getvalue())
                resume_text = pdf_info.text
                flags = run_all_checks(pdf_info)
            elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                resume_text = read_docx(resume_file.getvalue())
                # For DOCX, create a minimal PdfInfo for flags
                from core.pdf_reader import PdfInfo
                flags = []  # DOCX doesn't have layout issues like PDF
            else:
                st.error("Unsupported file type. Please upload a PDF or DOCX file.")
                st.stop()

            if not has_readable_text(resume_text):
                st.error("We couldn't read text from this file. Please ensure it's a text-based document.")
                st.stop()

            if resume_file.type == "application/pdf":
                flags = run_all_checks(pdf_info)

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

            # Validate and sanitize job label
            job_label_clean = job_label.strip()[:100] if job_label else None
            if job_label_clean and len(job_label_clean) == 0:
                job_label_clean = None
            db.record_usage(sb)
            db.save_analysis(
                sb,
                job_label_clean,
                overall,
                result.model_dump(),
                [dataclasses.asdict(f) for f in flags],
            )

            # Store everything in session state for persistence across reruns
            st.session_state["analysis_result"] = result
            st.session_state["overall_score"] = overall
            st.session_state["flags"] = flags
            st.session_state["resume_text"] = resume_text
            st.session_state["jd_text"] = jd_input

            # Extract confirmable items and store
            if result.confirmable_items:
                confirmable_items = result.confirmable_items
            else:
                confirmable_items = extract_confirmable_items(result)
            st.session_state["confirmable_items"] = confirmable_items

            # Rerun to show results with proper state
            st.rerun()
    else:
        st.warning("Please upload a resume and enter a job description.")