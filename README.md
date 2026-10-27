# Optima
## AI-Powered Resume Analyzer

Optima is a web application that uses a large language model (LLM) to analyze how well a resume matches a specific job description. Upload a resume as a PDF, paste a job description, and Optima scores the match, shows which requirements are met or missing, and suggests specific fixes, all in seconds.

**Recent Improvements:**
- ✅ Fixed critical cache logic bug for faster repeat analyses
- ✅ Optimized PDF text extraction with list comprehensions
- ✅ Added user authentication with Supabase
- ✅ Implemented proper logging system
- ✅ Added input validation and error handling
- ✅ Optimized string normalization with regex
- ✅ Added performance benchmarking tools
- ✅ Built rule-based remote application readiness checks
- ✅ Enhanced PDF inspection to detect layout issues (photos, columns, tables)
- ✅ Added unit tests for rule-based checks
- ✅ Implemented application readiness scoring system

---

### 🚀 Live Demo

👉 [Launch the App](https://optima-ai-resume-analyzer.streamlit.app/)

---

### 🧠 Features

**Analysis**
- **PDF Resume Processing:** Extracts text from uploaded PDF resumes with optimized string handling for faster processing.
- **PDF Layout Inspection:** Detects layout issues that hurt ATS readability (photos, multi-column layouts, tables) and provides specific fixes.
- **Scanned PDF Detection:** Detects image-only PDFs with no readable text and tells the user how to fix it, instead of sending empty text to the AI.
- **Requirements Checklist:** The AI lists the 10 most important requirements in the job description and marks each one as found or not found in the resume, quoting the evidence. Users can open the full checklist to see exactly why they were scored the way they were.
- **Consistent, Explainable Scoring:** The AI answers simple yes/no checks and rates experience and achievements on a defined 1-5 scale. The overall score is then calculated in code with fixed weights (requirements 60%, experience 25%, achievements 15%), with a plain-language label such as "Good match, with gaps to fix".
- **Prioritized Missing Requirements:** Each gap is marked high, medium or low priority, with a suggestion for adding it truthfully.
- **Strengths and Top Fixes:** Shows what the resume already does well, plus specific changes to make.
- **Result Caching:** Submitting the same resume and job description again returns the same result instantly, without another AI call (fixed to check cache before API call).

**Remote Application Readiness**
- **Rule-Based Checks:** Uses fixed rules (not AI) to check for common CV habits that hurt remote applications, ensuring consistent results and no API costs.
- **Personal Details Detection:** Flags unnecessary personal information (date of birth, age, marital status, religion, state of origin) that remote employers don't expect.
- **Contact Information Validation:** Checks for email, LinkedIn profile, and international phone format.
- **Section Heading Analysis:** Ensures standard ATS-friendly headings (Experience, Education, Skills) are present.
- **Remote Work Evidence:** Identifies mentions of remote tools (Slack, Zoom, Jira, etc.) and remote work experience.
- **Layout Analysis:** Detects photos, multi-column layouts, and tables that confuse ATS software.
- **Application Readiness Score:** Provides a 0-100 score based on the severity of issues found, with specific actionable fixes for each flag.

**User Accounts**
- **Secure Authentication:** User sign-up and sign-in with email/password using Supabase.
- **Session Management:** Maintains user sessions across page interactions.
- **Password Security:** Enforces minimum password length (8 characters).

**Reliability and safety**
- **Structured AI Output:** The AI returns JSON in a fixed format, validated with Pydantic. If a reply is invalid, Optima retries once with the error message included (with prompt length protection).
- **Prompt Injection Protection:** Resume and job text are placed inside clearly marked tags, cleaned with regex optimization so they cannot fake those tags, and treated as data rather than instructions. Wording that looks like instructions to an AI triggers a warning to the user.
- **Input Limits:** Caps resume uploads at 5 MB and job descriptions at 8,000 characters to control API costs.
- **Error Handling:** API timeouts and failures show a friendly message instead of crashing the app, with specific exception handling for better debugging.
- **Input Validation:** PDF files are validated before processing to prevent crashes from invalid uploads.
- **Structured Logging:** All errors and warnings are logged with timestamps and severity levels for production debugging.

---

### 📦 Built With

- [Python 3](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — web interface
- [OpenAI API](https://platform.openai.com/) — resume and job description analysis
- [Supabase](https://supabase.com/) — user authentication and database
- [Pydantic](https://docs.pydantic.dev/) — validation of the AI's structured output
- [PyMuPDF](https://pymupdf.readthedocs.io/) — text extraction from PDF resumes
- [python-dotenv](https://pypi.org/project/python-dotenv/) — secure API key management
- [pytest](https://docs.pytest.org/) — unit testing framework

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
3. **Set up your API keys**

   Create a `.env` file in the project folder (use `.env.example` as a template):
```
   OPENAI_API_KEY=your_openai_api_key_here
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

   **To get Supabase credentials:**
   - Go to [supabase.com](https://supabase.com) and create a free account
   - Create a new project
   - Go to Settings → API
   - Copy "Project URL" (ensure it doesn't include `/rest/v1` at the end)
   - Copy "anon public" key

   When deployed on Streamlit Cloud, add the keys under **Settings > Secrets** instead:
```
   OPENAI_API_KEY = "your_openai_api_key_here"
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
```
4. **Run the app**
```
   python -m streamlit run main.py
```

**Optional: Run tests**
```
   pytest tests/
```

---

### 📂 Project Structure

```
optima/
├── main.py                # Streamlit interface with authentication and analysis
├── benchmark.py          # Performance benchmarking tools
├── core/
│   ├── __init__.py
│   ├── pdf_reader.py      # PDF text extraction, layout inspection, and scanned-PDF detection
│   ├── prompts.py         # All AI prompt text, including security rules
│   ├── llm.py             # OpenAI calls, validation and retry with logging
│   ├── schemas.py         # Pydantic models describing a valid analysis
│   ├── scoring.py         # Weighted overall score, score labels, and readiness scoring
│   ├── safety.py          # Prompt injection cleaning and detection (regex optimized)
│   └── rules.py           # Rule-based checks for remote application readiness
├── services/
│   ├── __init__.py
│   └── auth.py            # User authentication with Supabase
├── tests/
│   └── test_rules.py      # Unit tests for rule-based checks
├── requirements.txt       # Dependencies
├── .env.example           # API key template (safe to commit)
├── .gitignore             # Keeps .env out of GitHub
└── README.md              # Project documentation
```

The `core/` folder contains the app's logic and never imports Streamlit, so it can be reused later (for example in a separate backend) without changes. The `services/` folder handles external integrations like authentication. The `tests/` folder contains unit tests for rule-based checks.

---

### 🗺️ Roadmap

Optima is being developed for **African job seekers applying to remote roles**.

**Completed:**
- ✅ User accounts with secure authentication
- ✅ Performance optimizations (caching, PDF extraction, string handling)
- ✅ Structured logging and error handling
- ✅ Input validation and security improvements
- ✅ Rule-based CV checks for remote applications (personal details, contact info, headings)
- ✅ ATS layout analysis (photos, columns, tables detection)
- ✅ Application readiness scoring system
- ✅ Unit tests for rule-based checks

**Planned work:**
- 🔄 Saved analysis history per user (database integration)
- Free-tier usage limits
- Enhanced ATS-readability checks (keyword matching, formatting)
- Bullet-point rewriter and tailored resume export
- Application tracker
- Local payment options and pricing

---

### 👤 Author
Ifedayo Steven Fakayode

Connect on [LinkedIn](https://www.linkedin.com/in/ifedayofakayode/)
