# ⚡ PromptCraft — Prompt Quality Evaluation & Learning System

An intelligent AI prompt evaluation and optimization platform built with **Streamlit**, **Google Gemini**, and **NLP evaluation pipelines**.


---

## 📌 Key Features

* **7-Dimensional Scoring**: Evaluates prompts on Grammar, Readability, Specificity, Context, Completeness, Ambiguity, and Constraints.
* **Multimodal Input**: Enter prompts via text, uploaded images (AI Vision OCR), or live voice recording (Whisper).
* **RAG Document Ingestion**: Upload reference documents (`.pdf`, `.docx`, `.txt`) for context-aware evaluations.
* **Intelligent Optimization**: Auto-generates production-grade, high-scoring rewritten prompts with side-by-side comparisons.
* **Multi-Key Failover**: Seamlessly rotates across multiple Gemini API keys to avoid rate-limit disruptions.

---

## 🚀 How to Run the Project

Run the following commands in **PowerShell**:

```powershell
.\venv\Scripts\activate
streamlit run app.py
```

Once started, open your browser and navigate to:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## ⚙️ Configuration

Ensure your Google Gemini API key is configured in your `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

*(Optional: Provide multiple comma-separated keys in `GEMINI_API_KEYS` for auto-failover).*

---

## 🛠️ Initial Setup (Fresh Environment Only)

If setting up on a new machine from scratch:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

