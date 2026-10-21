# IMPORT LIBRARIES
import streamlit as st
import fitz # PyMuPDF for reading PDF files
from openai import OpenAI
import os
from dotenv import load_dotenv

# LOAD API KEY
load_dotenv()
# OpenAI.api_key = os.getenv("OPENAI_API_KEY")
api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY"))

if not api_key:
    st.error("❌ OpenAI API key not found! Please set it in `.env` locally or Streamlit Secrets on cloud.")
    st.stop()

client = OpenAI(api_key=api_key)

#DEFINE A FUNCTION TO READ PDF RESUME
def extract_text_from_pdf(file ):
    with fitz.open(stream = file.read(), filetype= "pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text

# CREATE THE GPT PROMPT
def create_prompt(resume, job_description):
    return f"""
You are an expert career coach and ATS expert.
You MUST return valid JSON only.

Compare the Resume and Job Description.

Return JSON in this exact format:
{{
  "match_score": 85,
  "ats_score": 70,
  "missing_keywords": ["python", "sql", "team leadership"],
  "strengths": ["strong experience with...", "..."],
  "critical_gaps": ["No mention of..."],
  "improvements": ["Add keyword X to experience section", "Quantify achievement Y"]
}}

Resume:
{resume}

Job Description:
{job_description}
"""

# CALL GPT WITH OPENAI API
def analyze_resume(resume_text, jd_text):
    prompt = create_prompt(resume_text, jd_text)
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {"role": "system", "content": "You are a helpful HR assistant. You always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature = 0.4,
        max_tokens = 1500,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

# BUILD THE WEB INTERFACE WITH STREAMLIT
st.set_page_config(page_title="Optima", page_icon="🤖")
st.title("Optima")
st.write("**AI-Powered Resume Analyzer**")
st.write("Upload your resume and paste a job description. Let AI tell you how well you match!")

resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
jd_input = st.text_area("Paste the Job Description here", height=250)

#RUN THE ANALYSIS
analyze_button = st.button("Analyze Match")
if analyze_button:
    # Check for inputs only after the button is clicked
    if resume_file and jd_input:
        with st.spinner("Analyzing with AI..."):
            resume_text = extract_text_from_pdf(resume_file)
            result = analyze_resume(resume_text, jd_input)
            st.subheader("📋 AI Feedback:")
            st.markdown(result)
    else:
        st.warning("Please upload a resume and enter a job description.")