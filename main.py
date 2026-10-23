# IMPORT LIBRARIES
import hashlib
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from core.llm import analyze_resume
from core.pdf_reader import extract_text_from_pdf, has_readable_text

from core.scoring import compute_overall_score, requirements_score, score_band

MAX_FILE_SIZE_MB = 5  # Maximum file size in megabytes
MAX_CACHE_ENTRIES = 100  # Maximum number of entries to keep in the cache

# LOAD API KEY
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
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
st.set_page_config(page_title="Optima", page_icon="🤖")
st.title("Optima")
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
            resume_text = extract_text_from_pdf(resume_file)

            if not has_readable_text(resume_text):
                st.error("We couldn't read text from this PDF. Try exporting your resume as a text-based PDF from Word or Google Docs.")
                st.stop()

            cache = get_result_cache()
            key = hashlib.sha256((resume_text + "||" + jd_input).encode()).hexdigest()
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
    else:
        st.warning("Please upload a resume and enter a job description.")