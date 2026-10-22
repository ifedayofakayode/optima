# Optima
## AI-Powered Resume Analyzer

Optima is a web application that uses a large language model (LLM) to analyze how well a resume matches a specific job description. Upload a resume as a PDF, paste a job description, and Optima scores the match, highlights missing keywords by priority, and suggests specific fixes, all in seconds.

---

### 🚀 Live Demo

👉 [Launch the App](https://optima-ai-resume-analyzer.streamlit.app/)

---

### 🧠 Features

- **PDF Resume Processing:** Extracts text from uploaded PDF resumes.
- **Scanned PDF Detection:** Detects image-only PDFs that contain no readable text and tells the user how to fix it, instead of sending empty text to the AI.
- **Job Description Input:** Paste a job description directly into the app (up to 8,000 characters).
- **Structured AI Analysis:** The AI returns JSON in a fixed format, which is validated with Pydantic. If a reply is invalid, Optima retries once with the error message included.
- **Weighted Scoring:** The AI rates four areas (skills, experience, keywords, achievements), and the overall score is calculated in code with fixed weights (40% / 25% / 20% / 15%), alongside a plain-language label such as "Good match, with gaps to fix".
- **Prioritized Missing Keywords:** Each gap is marked high, medium or low priority, with an explanation of why it matters and a suggestion for adding it truthfully.
- **Strengths and Top Fixes:** Shows what the resume already does well, plus specific changes to make.
- **Input Limits:** Caps resume uploads at 5 MB and job descriptions at 8,000 characters to control API costs.
- **Error Handling:** API timeouts and failures show a friendly message instead of crashing the app.

---

### 📦 Built With

- [Python 3](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — web interface
- [OpenAI API](https://platform.openai.com/) — resume and job description analysis
- [Pydantic](https://docs.pydantic.dev/) — validation of the AI's structured output
- [PyMuPDF](https://pymupdf.readthedocs.io/) — text extraction from PDF resumes
- [python-dotenv](https://pypi.org/project/python-dotenv/) — secure API key management

---

### 🖥️ Run Locally

1. **Clone this repo**
```
   git clone https://github.com/ifedayofakayode/optima.git
   cd optima
```
2. **Install dependencies**
```
   python -m pip install -r requirements.txt
```
3. **Set up your API key**

   Create a `.env` file in the project folder (use `.env.example` as a template):
```
   OPENAI_API_KEY=your_openai_api_key_here
```
   When deployed on Streamlit Cloud, add the key under **Settings > Secrets** instead:
```
   OPENAI_API_KEY = "your_openai_api_key_here"
```
4. **Run the app**
```
   python -m streamlit run main.py
```

---

### 📂 Project Structure

```
optima/
├── main.py                # Streamlit interface (screen only)
├── core/
│   ├── __init__.py
│   ├── pdf_reader.py      # PDF text extraction and scanned-PDF detection
│   ├── prompts.py         # All AI prompt text
│   ├── llm.py             # OpenAI calls, validation and retry (change the model here)
│   ├── schemas.py         # Pydantic models describing a valid analysis
│   └── scoring.py         # Weighted overall score and score labels
├── requirements.txt       # Dependencies
├── .env.example           # API key template (safe to commit)
├── .gitignore             # Keeps .env out of GitHub
└── README.md              # Project documentation
```

The `core/` folder contains the app's logic and never imports Streamlit, so it can be reused later (for example in a separate backend) without changes.

---

### 🗺️ Roadmap

Optima is being developed for **African job seekers applying to remote roles**. Planned work:

- More consistent scoring across repeated runs of the same resume
- Checks for common CV habits that hurt remote applications (photo, date of birth, "career objective" statements)
- ATS-readability checks
- User accounts and saved analysis history
- Bullet-point rewriter and tailored resume export
- Application tracker
- Local payment options and pricing

---

### 👤 Author
Ifedayo Steven Fakayode

Connect on [LinkedIn](https://www.linkedin.com/in/ifedayofakayode/)
