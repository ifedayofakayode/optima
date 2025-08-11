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
You are an expert career coach and professional resume analyst with deep knowledge of recruitment best practices and Applicant Tracking Systems (ATS).
Your task is to evaluate how well a candidate's resume matches a given job description.

Instructions:
1.  Compare the **Resume** and **Job Description** provided below.
2.  Rate the overall match between the resume and the job description on a scale of 1 to 100, where:
    - 1 = extremely poor match
    - 100 = perfect match
3.  Identify the **key skilss, qualifications, certifications, or experiences** from the job description that are missing of insufficiently represented in the resume.
4.  Suggest **specific, actionable improvements** to the resume so it more closely aligns with the job description. Include:
    - Keywords or phrases to add
    - Sections to expand or adjust
    - Achievements or metrics to highlight
5.  Keep feedback concise but detailed enough to guide meaningful improvements.

Resume:
{resume}

Job desriptions:
{job_description}
"""

# CALL GPT WITH OPENAI API
def analyze_resume(resume_text, jd_text):
    prompt = create_prompt(resume_text, jd_text)
    client = OpenAI()
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {"role": "system", "content": "You are a helpful HR assistant"},
            {"role": "user", "content": prompt}
        ],
        temperature = 0.4,
        max_tokens = 800
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