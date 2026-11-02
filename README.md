# Optima
## AI-Powered Resume Analyzer

Optima is a web application that uses a large language model (LLM) to analyze how well a resume matches a specific job description. Upload a resume as a PDF, paste a job description, and Optima scores the match, shows which requirements are met or missing, and suggests specific fixes, all in seconds.

**Recent Improvements:**
- ✅ Fixed critical cache logic bug for faster repeat analyses
- ✅ Optimized PDF text extraction with list comprehensions
- ✅ Added user authentication with Supabase
- ✅ Implemented proper logging system throughout the application
- ✅ Added input validation and error handling
- ✅ Optimized string normalization with regex
- ✅ Added performance benchmarking tools
- ✅ Built rule-based remote application readiness checks
- ✅ Enhanced PDF inspection to detect layout issues (photos, columns, tables)
- ✅ Added unit tests for rule-based checks
- ✅ Implemented application readiness scoring system
- ✅ Integrated Supabase database for saving analysis history
- ✅ Added usage tracking with free monthly limits
- ✅ Implemented analysis history retrieval and management
- ✅ Built AI-powered bullet rewriter with number invention detection
- ✅ Integrated Sentry for production error monitoring
- ✅ Increased free tier limits (20 analyses, 30 rewrites per month)
- ✅ Fixed dependency versioning in requirements.txt for stable deployments
- ✅ Enhanced password policy with complexity requirements (uppercase, lowercase, numbers)
- ✅ Added email format validation for authentication
- ✅ Implemented rate limiting (10 calls per minute) to prevent API abuse
- ✅ Improved cache eviction to use LRU (Least Recently Used) algorithm
- ✅ Enhanced error messages with context and troubleshooting guidance
- ✅ Added job label validation to prevent database abuse
- ✅ Fixed OpenAI model configuration to use valid model names
- ✅ Improved session security by removing credentials from session state
- ✅ Expanded test coverage for auth, safety, and scoring modules
- ✅ Added GitHub Actions CI/CD pipeline for automated testing
- ✅ **Implemented Gap Confirmation Flow** - Users can confirm missing skills/experience before generation
- ✅ **Built Tailored Resume Generation** - AI-powered resume rewriting with fabrication guardrails
- ✅ **Added Cover Letter Generation** - Non-generic, evidence-based cover letters with banned phrase detection
- ✅ **Implemented Resume Parsing** - Structured extraction of resume data using LLM
- ✅ **Enhanced Analysis Output** - Added ATS score, keyword grouping, critical gaps, and format issues
- ✅ **Added PDF Export** - Automated PDF generation with selectable text
- ✅ **Added DOCX Upload Support** - Users can now upload both PDF and DOCX resumes

---

### 🚀 Live Demo

👉 [Launch the App](https://optima-ai-resume-analyzer.streamlit.app/)

---

### 🧠 Features

**Analysis**
- **PDF & DOCX Resume Processing:** Extracts text from uploaded PDF or DOCX resumes with optimized string handling for faster processing.
- **PDF Layout Inspection:** Detects layout issues that hurt ATS readability (photos, multi-column layouts, tables) and provides specific fixes.
- **Scanned PDF Detection:** Detects image-only PDFs with no readable text and tells the user how to fix it, instead of sending empty text to the AI.
- **Requirements Checklist:** The AI lists the 10 most important requirements in the job description and marks each one as found or not found in the resume, quoting the evidence. Users can open the full checklist to see exactly why they were scored the way they were.
- **Consistent, Explainable Scoring:** The AI answers simple yes/no checks and rates experience and achievements on a defined 1-5 scale. The overall score is then calculated in code with fixed weights (requirements 60%, experience 25%, achievements 15%), with a plain-language label such as "Good match, with gaps to fix".
- **ATS Score Analysis:** Provides an ATS compatibility score (0-100) with explanation, identifying format issues and keyword gaps that could hurt ATS parsing.
- **Keyword Grouping:** Separates missing keywords into must-have vs nice-to-have categories for prioritized improvement.
- **Critical Gaps Identification:** Highlights requirements that, if missing, would likely cause rejection vs general improvement suggestions.
- **Prioritized Missing Requirements:** Each gap is marked high, medium or low priority, with a suggestion for adding it truthfully.
- **Strengths and Top Fixes:** Shows what the resume already does well, plus specific changes to make.
- **Result Caching:** Submitting the same resume and job description again returns the same result instantly, without another AI call. Uses LRU (Least Recently Used) eviction to keep frequently-used results in cache.

**Bullet Rewriter**
- **AI-Powered Bullet Enhancement:** Transforms weak resume bullets into stronger, impact-focused versions using AI.
- **Number Invention Detection:** Automatically detects and blocks rewrites that invent numbers not present in the original, ensuring honesty.
- **Bracketed Placeholders:** Uses [square brackets] for any numbers that need to be filled in, helping users identify where to add their real metrics.
- **Multiple Rewrite Approaches:** Provides 3 different rewrite styles: "Results first", "Action and scope", and "Concise".
- **Weakness Analysis:** Identifies specific weaknesses in the original bullet and provides targeted questions to help users find their real numbers.
- **Optional PDF Bullet Extraction:** Users can upload their resume PDF to automatically extract and select bullet points for rewriting.
- **Safety Filtering:** Only returns rewrites that don't invent numbers, with automatic retry logic if the AI produces unsafe content.

**Gap Confirmation Flow**
- **Missing Requirements Confirmation:** Presents missing JD requirements as a checklist with Yes/Partially/No options.
- **Evidence Collection:** For confirmed items, collects user-provided evidence (years, context, projects).
- **Honesty Summary:** Shows what's kept from original resume, what's added from confirmations, and what's excluded as honest gaps.
- **Conservative Phrasing:** "Partially" confirmed items are phrased conservatively in generation (e.g., "Familiar with" vs "Expert in").
- **Traceability:** Only confirmed items flow into resume generation, ensuring 100% traceability of claims.

**Tailored Resume Generation**
- **AI-Powered Resume Rewriting:** Automatically rewrites resumes to match job descriptions with strong, impact-focused bullets.
- **Fabrication Guardrails:** Never invents employers, titles, dates, degrees, certifications, tools, skills, or metrics.
- **Placeholder Metrics:** Uses [X%], [number], [months] style placeholders for missing metrics instead of inventing numbers.
- **JD Keyword Integration:** Naturally integrates job description keywords without keyword stuffing.
- **Skills Ordering:** Orders skills by relevance to the job description.
- **ATS-Friendly Structure:** Ensures single-column layout, standard headings, no tables/columns/photos.
- **Inline Editing:** Full inline editing of all resume sections before download.
- **Dual Export:** Download as both DOCX and PDF with selectable text.

**Cover Letter Generation**
- **Non-Generic Generation:** Creates tailored cover letters based on resume profile, JD, and confirmed items.
- **Evidence-Based Content:** Each body paragraph references specific JD requirements and concrete achievements.
- **Banned Phrase Detection:** Automatically avoids 13 common clichés like "passionate team player" and "I am writing to express my interest".
- **Structured Format:** Enforces hook → 2 evidence-based body paragraphs → brief closing structure.
- **Word Count Target:** Targets 250-350 words with validation and display.
- **Optional Customization:** Supports tone selection (professional, warm, confident), hiring manager name, and "why this company" input.
- **Inline Editing:** Full-text and individual section editing before download.
- **DOCX Export:** Properly formatted cover letter document export.

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
- **Password Security:** Enforces strong password requirements (8+ characters with uppercase, lowercase, and numbers).
- **Email Validation:** Validates email format before submission to prevent errors.
- **Analysis History:** Saves all resume analyses to Supabase database for later review.
- **Usage Tracking:** Tracks monthly usage with free-tier limits (20 analyses and 30 rewrites per month).
- **Rate Limiting:** Implements rate limiting (10 calls per minute) to prevent API abuse.
- **History Management:** Users can view, delete, and manage their saved analyses.

**Reliability and safety**
- **Structured AI Output:** The AI returns JSON in a fixed format, validated with Pydantic. If a reply is invalid, Optima retries once with the error message included (with prompt length protection).
- **Prompt Injection Protection:** Resume and job text are placed inside clearly marked tags, cleaned with regex optimization so they cannot fake those tags, and treated as data rather than instructions. Wording that looks like instructions to an AI triggers a warning to the user.
- **Input Limits:** Caps resume uploads at 5 MB and job descriptions at 8,000 characters to control API costs.
- **Error Handling:** API timeouts and failures show a friendly message instead of crashing the app, with specific exception handling for better debugging.
- **Input Validation:** PDF files are validated before processing to prevent crashes from invalid uploads.
- **Structured Logging:** All errors and warnings are logged with timestamps and severity levels for production debugging.
- **Production Error Monitoring:** Integrated Sentry SDK to capture and report exceptions for real-time production debugging and error tracking.

---

### 📦 Built With

- [Python 3](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — web interface
- [OpenAI API](https://platform.openai.com/) — resume and job description analysis
- [Supabase](https://supabase.com/) — user authentication and database
- [Pydantic](https://docs.pydantic.dev/) — validation of the AI's structured output
- [PyMuPDF](https://pymupdf.readthedocs.io/) — text extraction from PDF resumes
- [python-docx](https://python-docx.readthedocs.io/) — Word document processing
- [python-dotenv](https://pypi.org/project/python-dotenv/) — secure API key management
- [Sentry SDK](https://sentry.io/) — production error monitoring
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
   OPENAI_MODEL=gpt-4o-mini  # Optional: defaults to gpt-4o-mini if not set
```

   **To get Supabase credentials:**
   - Go to [supabase.com](https://supabase.com) and create a free account
   - Create a new project
   - Go to Settings → API
   - Copy "Project URL" (ensure it doesn't include `/rest/v1` at the end)
   - Copy "anon public" key

   **Set up database tables:**
   - In your Supabase project, go to SQL Editor
   - Run the SQL commands to create the `analyses` and `usage` tables (see Database Setup section below)

   When deployed on Streamlit Cloud, add the keys under **Settings > Secrets** instead:
```
   OPENAI_API_KEY = "your_openai_api_key_here"
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
   OPENAI_MODEL = "gpt-4o-mini"  # Optional
```
4. **Run the app**
```
   python -m streamlit run main.py
```

**Optional: Run tests**
```
   pytest tests/
```

**Note:** The project includes a GitHub Actions workflow that automatically runs tests on push and pull requests to ensure code quality.

---

### 🗄️ Database Setup

After setting up your Supabase project, you need to create the required tables. Run this SQL in your Supabase SQL Editor:

```sql
-- Create the usage table (tracks monthly usage)
CREATE TABLE public.usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    kind TEXT DEFAULT 'analysis',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- If you already have a usage table without the 'kind' column, run this migration:
ALTER TABLE public.usage ADD COLUMN kind TEXT DEFAULT 'analysis';
UPDATE public.usage SET kind = 'analysis' WHERE kind IS NULL;

-- Create the analyses table (stores analysis results)
CREATE TABLE public.analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    job_label TEXT,
    overall_score INTEGER NOT NULL,
    result JSONB NOT NULL,
    flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;

-- Create policies for usage table
CREATE POLICY "Users can view their own usage"
    ON public.usage FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own usage"
    ON public.usage FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policies for analyses table
CREATE POLICY "Users can view their own analyses"
    ON public.analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analyses"
    ON public.analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own analyses"
    ON public.analyses FOR DELETE
    USING (auth.uid() = user_id);
```

---

### � Database Migrations

Database schema changes are tracked in `MIGRATIONS.md`. When deploying updates, check this file for any SQL commands that need to be run on your Supabase database.

---

### �📂 Project Structure

```
optima/
├── main.py                # Streamlit interface with authentication, analysis, and bullet rewriter
├── benchmark.py          # Performance benchmarking tools
├── core/
│   ├── __init__.py
│   ├── pdf_reader.py      # PDF text extraction, layout inspection, and scanned-PDF detection
│   ├── prompts.py         # All AI prompt text, including security rules
│   ├── llm.py             # OpenAI calls, validation and retry with logging
│   ├── schemas.py         # Pydantic models describing a valid analysis and rewrite results
│   ├── scoring.py         # Weighted overall score, score labels, and readiness scoring
│   ├── safety.py          # Prompt injection cleaning and detection (regex optimized)
│   ├── rules.py           # Rule-based checks for remote application readiness
│   └── rewriter.py        # AI-powered bullet rewriter with number invention detection
├── services/
│   ├── __init__.py
│   ├── auth.py            # User authentication with Supabase
│   └── db.py              # Database operations (usage tracking, analysis history)
├── tests/
│   ├── test_rules.py      # Unit tests for rule-based checks
│   ├── test_rewriter.py   # Unit tests for bullet rewriter
│   ├── test_auth.py       # Unit tests for authentication validation
│   ├── test_safety.py     # Unit tests for prompt injection detection
│   └── test_scoring.py    # Unit tests for scoring algorithms
├── requirements.txt       # Dependencies with version pins
├── .env.example           # API key template (safe to commit)
├── .gitignore             # Keeps .env out of GitHub
├── MIGRATIONS.md          # Database schema change history
└── README.md              # Project documentation
```

The `core/` folder contains the app's logic and never imports Streamlit, so it can be reused later (for example in a separate backend) without changes. The `services/` folder handles external integrations like authentication and database operations. The `tests/` folder contains unit tests for rule-based checks and the bullet rewriter.

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
- ✅ Database integration for saving analysis history
- ✅ Usage tracking with free monthly limits
- ✅ Analysis history retrieval and management
- ✅ AI-powered bullet rewriter with number invention detection
- ✅ Sentry integration for production error monitoring
- ✅ Increased free tier limits (20 analyses, 30 rewrites per month)
- ✅ Dependency versioning for stable deployments
- ✅ Enhanced password security with complexity requirements
- ✅ Email validation for authentication
- ✅ Rate limiting to prevent API abuse
- ✅ LRU cache implementation for better performance
- ✅ Improved error messages with context
- ✅ Session security improvements
- ✅ Expanded test coverage
- ✅ CI/CD pipeline with automated testing

**Planned work:**
- Enhanced ATS-readability checks (keyword matching, formatting)
- Tailored resume export to Word/DOCX
- Application tracker
- Local payment options and pricing
- Premium tier with higher limits
- Additional test coverage for database and authentication flows

---

### 👤 Author
Ifedayo Steven Fakayode

Connect on [LinkedIn](https://www.linkedin.com/in/ifedayofakayode/)
