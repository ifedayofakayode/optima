# IMPORT LIBRARIES
import json
import streamlit as st
import fitz  # PyMuPDF for reading PDF files
from openai import OpenAI
import os
from dotenv import load_dotenv

MAX_FILE_SIZE_MB = 5  # Maximum file size in megabytes

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

client = OpenAI(api_key=api_key, timeout=30)

# DEFINE A FUNCTION TO READ PDF RESUME
def extract_text_from_pdf(file):
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text

# CREATE THE GPT PROMPT
def create_prompt(resume, job_description):
    return f"""
You are an expert career coach and ATS expert.
Compare the Resume and Job Description below.

You MUST return valid JSON only, using exactly these keys:
- "match_score": integer from 0 to 100 (how well the resume fits the job)
- "ats_score": integer from 0 to 100 (how easily an ATS can read and match the resume)
- "missing_keywords": list of important keywords from the job description that are missing from the resume
- "strengths": list of short statements about what the resume does well for this job
- "critical_gaps": list of the most serious missing qualifications or experience
- "improvements": list of specific, actionable changes to the resume

Base every value on the actual Resume and Job Description. Do not invent experience.

Resume:
{resume}

Job Description:
{job_description}
"""

# CALL GPT WITH OPENAI API
def analyze_resume(resume_text, jd_text):
    prompt = create_prompt(resume_text, jd_text)
    try:
        response = client.chat.completions.create(
            model="gpt-6-luna",
            messages=[
                {"role": "system", "content": "You are a helpful HR assistant. Reply with JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=4000,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Analysis error: {e}")
        return None

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

            if len(resume_text.strip()) < 200:
                st.error("We couldn't read text from this PDF. Try exporting your resume as a text-based PDF from Word or Google Docs.")
                st.stop()

            result = analyze_resume(resume_text, jd_input)

        if result is None:
            st.error("Something went wrong while analyzing your resume. Please try again in a moment.")
        else:
            st.subheader("📋 AI Feedback")

            col1, col2 = st.columns(2)
            col1.metric("Match Score", f"{result.get('match_score', 0)}/100")
            col2.metric("ATS Score", f"{result.get('ats_score', 0)}/100")

            st.markdown("### ✅ Strengths")
            for item in result.get("strengths", []):
                st.write(f"- {item}")

            st.markdown("### ⚠️ Critical Gaps")
            for item in result.get("critical_gaps", []):
                st.write(f"- {item}")

            st.markdown("### 🔑 Missing Keywords")
            keywords = result.get("missing_keywords", [])
            st.write(", ".join(keywords) if keywords else "None found.")

            st.markdown("### 🛠 Suggested Improvements")
            for item in result.get("improvements", []):
                st.write(f"- {item}")
    else:
        st.warning("Please upload a resume and enter a job description.")