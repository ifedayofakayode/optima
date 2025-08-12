# Optima
## AI-Powered Resume Analyzer

This project is a web application that uses a large language model (LLM) to analyze how well a resume matches a specific job description. Users can upload a resume in PDF format and paste a job description, and the application will highlights missing skills, suggests improvements, and rate how well your resume matches the role — all in seconds.

---

### 🚀 Live Demo

👉 [Launch the App](https://optima-ai-resume-analyzer.streamlit.app/)

---

### 🧠 Features

- **PDF Resume Processing:** Accepts and extracts text from PDF files.
- **Job Description Input:** Allows users to paste or type a job description directly into the app.
- **AI-Powered Matching:** Utilizes OPENAI's API to compare the resume and job description.
- **Comprehensive Feedback:** Generates a sub-header with the AI Feedback in the UI.

---

### 📦 Built With

- [Python 3](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — for the web interface
- [OpenAI API](https://platform.openai.com/) — GPT-40-mini for analysis
- [PyMuPDF](https://pymupdf.readthedocs.io/) — for extracting text from PDF resumes
- [python-dotenv](https://pypi.org/project/python-dotenv/) — to securely manage API keys

---

### 🖥️ Run Locally

1. **Clone this repo**  
   ```
   git clone https://github.com/ifedayofakayode/optima.git
   cd optima
   ```
2. **Install dependencies**
  ```
  pip install -r requirements.txt
  ```
3. **Set up API Key**
Create a .env file in the project folder:
  ```
  OPENAI_API_KEY=your_openai_api_key_here
  ```
4. **Run the app**
  ```
  streamlit run main.py
  ```

---

### 📂 Project Structure
  ```
  ├── main.py                # Main Streamlit app
  ├── requirements.txt       # Dependencies
  ├── README.md              # Project documentation
  └── .env                   # OpenAI API key (not committed to GitHub)
  ```

---

### 👤 Author
Ifedayo Steven Fakayode

Connect on [LinkedIn](https://www.linkedin.com/in/ifedayofakayode/)
