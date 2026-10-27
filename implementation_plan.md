# Implementation Plan - PromptCraft

**PromptCraft** is a prompt quality evaluation, optimization, and learning system. It is designed to evaluate the quality of user prompts before they are submitted to an AI, identify weaknesses, explain why they are weak, provide a quality score, recommend improvements, automatically generate an improved version, and teach users how to write better prompts.

---

## 1. MULTIMODAL PROMPT INPUT & REFERENCE MATERIAL PLAN

PromptCraft supports multimodal prompt acquisition and optional reference materials. These two processing streams are kept completely separate.

### A. Actual User Prompt Acquisition
The actual user prompt is evaluated by the Evaluation Engine. It must be provided in one of exactly three ways:
1. **Text Input**: Direct entry in a Streamlit text area.
2. **Image Input**: Uploaded screenshot/photo processed via OCR (`pytesseract`).
3. **Live Voice UX**: Live microphone recording transcribed using OpenAI Whisper.
   * *User Review*: The transcribed voice prompt is displayed to the user for optional editing/correction or re-recording. It enters the evaluation pipeline only after user confirmation.
   * *Input Metadata*: The origin method is logged as `"text"`, `"image"`, or `"live_voice"`.

### B. Optional Reference Material (RAG)
Reference documents provide domain context to help the downstream LLM optimize the prompt.
* **Supported Formats**: PDF (`PyMuPDF/fitz`), Image (`pytesseract`), and DOCX (`python-docx`).
* **Strict Scoring Boundary**: Reference materials **MUST NOT** impact the Evaluation Engine's numerical scores. The Evaluation Engine evaluates ONLY the prompt itself.
* **RAG Pipeline**:
  ```text
  Uploaded Document (PDF/DOCX/Image)
         ↓
  Text Extraction & Cleaning
         ↓
  Text Chunking
         ↓
  Embedding Generation (Gemini Embeddings Model)
         ↓
  MongoDB Atlas Vector Search
         ↓
  Retrieved Chunks (Context) sent ONLY to the LLM
  ```

---

## 2. PREPROCESSING MODULE PLAN

The preprocessing module is responsible **ONLY** for preparing the user's prompt for the Evaluation Engine.

### Core Boundaries
The preprocessing module must **NOT**:
* Evaluate prompt quality or assign scores.
* Detect weaknesses or explain causes of weaknesses.
* Suggest improvements.
* Generate an optimized prompt or call the LLM for prompt improvement.

### The Most Important Rule: Preserve the Original Prompt
The original prompt must never be overwritten or modified. It must remain available for display, history, database storage, and comparisons.
* `original_prompt`: Stores exactly what the user entered (including leading/trailing whitespace, multiple spaces, capitalization, acronyms, and structure).

### Preprocessing Architecture & Flow
```text
USER INPUT (Text / Voice [Whisper] / Image [OCR] / Document [PDF/DOCX/TXT])
    ↓
Text Extraction (If multimodal)
    ↓
Step 0: Input Validation
    ↓
Step 1: Text Cleaning (Regex)
    ↓
Step 2: Case Normalization (Lowercase Analytical Copy)
    ↓
Step 3: Tokenization (spaCy)
    ↓
Step 4: Stop Word Handling (spaCy Stop-Word Tagging)
    ↓
Step 5: Sentence Segmentation (spaCy)
    ↓
Structured Preprocessed Data
    ↓
Evaluation Engine
```

---

## 3. PROMPT EVALUATION ENGINE PLAN

The **Prompt Evaluation Engine** has ONLY ONE responsibility: quantitatively evaluate the quality of a user's prompt across seven predefined parameters. It does NOT use LLM calls for scoring; it relies strictly on NLP tools and custom heuristics.

### Core Boundaries
The Evaluation Engine **MUST NOT**:
* Identify weaknesses in natural language or explain causes of weaknesses.
* Suggest improvements.
* Rewrite the prompt or generate an optimized prompt.
* Ask an LLM to decide the evaluation score.

These tasks will be performed separately by the LLM **AFTER** the Evaluation Engine finishes.

### The 7 Quality Parameters & Rule-Based Scoring

#### A. Grammar (`backend/grammar_analyzer.py`)
* **AI/Tool Used**: `LanguageTool` error count.
* **Scoring Rules**:
  * $0 \text{ errors} \rightarrow 10/10$
  * $1 \text{ error} \rightarrow 8/10$
  * $2\text{--}4 \text{ errors} \rightarrow 5/10$
  * $5+ \text{ errors} \rightarrow 2/10$
* **Evidence**: Stores raw count: `grammar_errors`.

#### B. Readability (`backend/readability_analyzer.py`)
* **AI/Tool Used**: `textstat` (Flesch Reading Ease score).
* **Scoring Rules**:
  * $\text{Flesch Score} > 70 \rightarrow 10/10$
  * $\text{Flesch Score} > 50 \text{ and } \le 70 \rightarrow 7/10$
  * $\text{Flesch Score} \le 50 \rightarrow 4/10$
* **Evidence**: Stores raw score: `flesch_reading_ease`.

#### C. Specificity (`backend/specificity_analyzer.py`)
* **AI/Tool Used**: `spaCy` NLP + Custom rule-based indicators.
* **Indicators Checked (10 Items)**:
  1. Clearly defined action/task
  2. Specific subject/topic
  3. Specific subtopic
  4. Target audience
  5. Required depth/level
  6. Desired output type
  7. Required content/components
  8. Examples explicitly requested
  9. Scope specified
  10. Purpose/use case specified
  *(Each detected indicator = 1 point. Max = 10).*
* **Scoring Rules**:
  * $0\text{--}1 \text{ indicators} \rightarrow 2/10$
  * $2\text{--}3 \text{ indicators} \rightarrow 4/10$
  * $4\text{--}5 \text{ indicators} \rightarrow 6/10$
  * $6\text{--}7 \text{ indicators} \rightarrow 8/10$
  * $8\text{--}10 \text{ indicators} \rightarrow 10/10$
* **Evidence**: Stores boolean dict: `features_detected`.

#### D. Context (`backend/context_analyzer.py`)
* **AI/Tool Used**: `spaCy` NLP + Custom rule-based categories.
* **Categories Checked (5 Items)**:
  1. Background information
  2. Purpose/goal
  3. User/audience context
  4. Domain/subject context
  5. Situation/use-case
  *(Each category detected = 2 points. Max = 10).*
* **Scoring Rules**:
  * $0\text{--}2 \text{ points} \rightarrow 2/10$
  * $3\text{--}4 \text{ points} \rightarrow 4/10$
  * $5\text{--}6 \text{ points} \rightarrow 6/10$
  * $7\text{--}8 \text{ points} \rightarrow 8/10$
  * $9\text{--}10 \text{ points} \rightarrow 10/10$
* **Evidence**: Stores boolean dict: `features_detected`.

#### E. Completeness (`backend/completeness_analyzer.py`)
* **AI/Tool Used**: `spaCy` NLP + Custom rule-based components.
* **Components Checked (5 Items)**:
  1. Clear task/instruction
  2. Subject/topic
  3. Expected output
  4. Required content/details
  5. Necessary specifications
  *(Each component detected = 2 points. Max = 10).*
* **Scoring Rules**:
  * $0\text{--}2 \text{ points} \rightarrow 2/10$
  * $3\text{--}4 \text{ points} \rightarrow 4/10$
  * $5\text{--}6 \text{ points} \rightarrow 6/10$
  * $7\text{--}8 \text{ points} \rightarrow 8/10$
  * $9\text{--}10 \text{ points} \rightarrow 10/10$
* **Evidence**: Stores boolean dict: `components_detected`.

#### F. Ambiguity (`backend/ambiguity_analyzer.py`)
* **AI/Tool Used**: `spaCy` NLP + Custom weighted dictionary.
* **Dictionary Weights**:
  * **Level 1 (Mild, Weight = 1)**: `some`, `several`, `appropriate`, `relevant`, `suitable`, `reasonable`
  * **Level 2 (Moderate, Weight = 2)**: `detailed`, `briefly`, `properly`, `effectively`, `clearly`, `good`, `simple`, `quickly`
  * **Level 3 (Strong, Weight = 3)**: `make it better`, `explain it well`, `give a good answer`, `improve this`, `do it properly`, `best possible`, `as needed`
  *(ambiguity_penalty = sum of weights for detected terms).*
* **Scoring Rules** *(High Score = Low Ambiguity)*:
  * $\text{Penalty } 0 \rightarrow 10/10$
  * $\text{Penalty } 1\text{--}2 \rightarrow 8/10$
  * $\text{Penalty } 3\text{--}4 \rightarrow 6/10$
  * $\text{Penalty } 5\text{--}6 \rightarrow 4/10$
  * $\text{Penalty } 7+ \rightarrow 2/10$
* **Evidence**: Stores terms list with weights: `terms_detected`.

#### G. Constraints (`backend/constraints_analyzer.py`)
* **AI/Tool Used**: `spaCy` NLP + Custom rule-based categories.
* **Categories Checked (5 Items)**:
  1. Length/word limit
  2. Output format/structure
  3. Tone/style
  4. Audience/level
  5. Quantity/specific requirements
  *(Each category detected = 2 points. Max = 10).*
* **Scoring Rules**:
  * $0\text{--}2 \text{ points} \rightarrow 2/10$
  * $3\text{--}4 \text{ points} \rightarrow 4/10$
  * $5\text{--}6 \text{ points} \rightarrow 6/10$
  * $7\text{--}8 \text{ points} \rightarrow 8/10$
  * $9\text{--}10 \text{ points} \rightarrow 10/10$
* **Evidence**: Stores boolean dict: `features_detected`.

### Aggregated Scoring & Overall Score (`backend/scoring_engine.py`)
Equal weighting is applied. Total is divided by 70 and scaled to 100, rounded to the nearest integer.

$$\text{Overall Score} = \text{round}\left( \frac{\text{Grammar} + \text{Readability} + \text{Specificity} + \text{Context} + \text{Completeness} + \text{Ambiguity} + \text{Constraints}}{70} \times 100 \right)$$

---

## 4. LLM ANALYSIS & OPTIMIZATION MODULE PLAN

The LLM is the second intelligence layer, responsible for qualitative interpretation and prompt rewriting.

### Core Boundaries
The LLM **MUST NOT**:
* Calculate evaluation scores or override scores produced by the Evaluation Engine.
* Replace the Evaluation Engine or invent scores.
* Perform RAG or search external knowledge bases for optimization.
* Change the user's original objective or intention.

### LLM Input Payload
The LLM is invoked once with:
* `original_prompt`: The unmodified user input.
* `evaluation_results`: The structured scores with preserved evidence/metadata.
* `overall_score`: The aggregated score out of 100.
* `reference_context` *(Optional)*: Semantically relevant chunks retrieved via Vector Search from uploaded references.

### LLM Structured JSON Response Schema
```json
{
    "parameter_analysis": [
        {
            "parameter": "Grammar",
            "score": 10,
            "status": "Strong",
            "weakness": null,
            "cause": null,
            "improvement": null
        },
        ...
    ],
    "overall_analysis": "...",
    "optimized_prompt": "..."
}
```

---

## 5. COMPLETE UI DESIGN & NAVIGATIONAL LAYOUT

The application implements a consistent, responsive, modern SaaS dashboard theme with a **purple/indigo primary brand color**, rounded cards, soft borders, and a persistent application shell.

### Persistent Application Shell Layout
* **Left**: Persistent navigation sidebar.
* **Top**: Header and navbar with PromptCraft branding.
* **Center**: Main content workspace, changing dynamically according to the sidebar selection.

### Left Sidebar Navigation Structure
```text
PROMPTCRAFT

MAIN
🏠 Dashboard

CREATE
✨ New Evaluation
📚 Reference Material

RESULTS
📊 Evaluation Results
🤖 LLM Analysis
✨ Optimized Prompt

HISTORY
🕘 Past Evaluations
🔖 Saved Prompts
```

---

## 6. PROPOSED PROJECT STRUCTURE

```text
PromptCraft1/
│
├── app.py                      # Main entry point of the app (Streamlit navigation)
│
├── pages/                      # Streamlit Pages
│   ├── 1_Home.py
│   ├── 2_Analyze_Prompt.py
│   ├── 3_Voice_Prompt.py
│   ├── 4_Image_Prompt.py
│   ├── 5_Document_Prompt.py
│   ├── 6_Prompt_History.py
│   ├── 7_Learning_Center.py
│   ├── 8_Recommendations.py
│   ├── 9_Dashboard.py
│   └── 10_About.py
│
├── backend/                    # Evaluation & Extraction Logic
│   ├── __init__.py
│   ├── preprocessing.py        # Implementation of Preprocessing Steps 0-5
│   ├── evaluation_engine.py    # Directs evaluation across modules
│   ├── scoring_engine.py       # Computes percentage and quality levels
│   ├── grammar_analyzer.py      # LanguageTool-based analysis
│   ├── readability_analyzer.py  # Flesch Reading Ease score via textstat
│   ├── specificity_analyzer.py  # spaCy-based specificity heuristics
│   ├── context_analyzer.py      # Rules + semantic evaluation
│   ├── completeness_analyzer.py # Checks for missing requirements
│   ├── ambiguity_analyzer.py    # Vague word list scan & pronoun check
│   ├── constraints_analyzer.py  # Constraints checklist
│   ├── vague_word_detector.py   # Dict-based vague term finder
│   ├── improvement_engine.py    # Weakness-driven recommendations
│   ├── prompt_rewriter.py      # LLM rewritten prompt generator
│   ├── recommendation_engine.py # Template manager
│   ├── learning_engine.py       # Topic recommendations
│   ├── rag_engine.py           # RAG retrieval module
│   ├── llm_service.py          # Google Gemini Provider
│   ├── whisper_service.py      # Speech-to-text conversion
│   ├── ocr_service.py          # Image-to-text conversion
│   └── document_processor.py   # PDF/DOCX/TXT text extractor
│
├── database/                   # Database Connectivity
│   ├── __init__.py
│   ├── mongodb.py              # MongoDB Atlas connection
│   └── repositories.py         # Repositories for Prompt, Feedback, learning logs
│
├── config/                     # Settings
│   └── settings.py             # Score thresholds, configs, environment loading
│
├── utils/                      # Utilities
│   ├── validators.py
│   └── helpers.py
│
├── data/                       # Static Assets
│   ├── vague_words.json
│   ├── learning_content.json
│   └── prompt_templates.json
│
├── .env                        # Secret environment variables
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 7. VERIFICATION PLAN

### Preprocessing Tests
* Test empty or whitespace prompts to verify Step 0 validation errors.
* Verify spacing cleanups, case matching, tokenizer output matching standard spaCy lists, stop word tagging correctness, and sentence breakdown splits.

### Evaluation Engine Tests
* Verify LanguageTool score mappings ($0\rightarrow 10$, $1\rightarrow 8$, $2\text{--}4\rightarrow 5$, $5+\rightarrow 2$).
* Verify Flesch score readability mappings ($>70\rightarrow 10$, $50\text{--}70\rightarrow 7$, $\le 50\rightarrow 4$).
* Verify Specificity Indicator checklist logic (1 point per indicator detected).
* Verify Context & Completeness checklist logic (2 points per category detected).
* Verify Ambiguity weighted dictionary penalties (Weights: 1, 2, 3) and score calculations.
* Verify Constraints checklist logic (2 points per constraint detected).
* Confirm that Overall score matches equal weighting math rounded to the nearest integer.

### LLM Module Tests
* Verify LLM correctly identifies weakness status for scores under 7.
* Verify LLM optimized prompt preserves intent (e.g. comparison prompt stays a comparison).
* Test malformed JSON parser recovery and retry handler.
* Test score consistency validator against modified LLM outputs.

### Multimodal & Reference Tests
* Test voice recorder UI layouts (State changes: Listening, Transcription, Review).
* Test document processors (`fitz` for PDF, `python-docx` for DOCX) on blank, standard, and corrupted files.
* Test OCR text extraction using mock images.
* Verify Vector Search query matching retrieved nodes against simple index filters in MongoDB Atlas.
* Confirm that uploading reference material has zero effect on the numerical scoring returned by the Evaluation Engine.
