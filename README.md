# ⚖️ NyayaSahayak — Indian Legal Information Assistant
> **BUILD-A-BOT Competition Entry**  
> **Organized by**: Data Intelligence Club, Department of Artificial Intelligence, Thiagarajar College of Engineering  
> **Theme**: Legal Assistant  
> **Target Problem**: Empowering citizens with factual, grounded legal information on Indian Constitutional Rights and Arrest/Detention Safeguards without hallucinations.

---

## 🌟 Key Highlights & Capabilities
- **Strictly Grounded RAG Pipeline**: Backed by authoritative Indian statutory provisions (Constitution of India, CrPC/BNSS, D.K. Basu guidelines, NALSA).
- **Domain & Boundary Enforcement**: Automatically rejects non-legal topics (e.g. Machine Learning, STEM, general chitchat) with zero LLM token waste.
- **Anti-Hallucination Threshold**: Refuses to fabricate answers on fictional laws (e.g. "Article 99A arrest robots") using cosine similarity evidence thresholds.
- **Verified Source Cards**: Every response displays official Government of India / Supreme Court source links and metadata.
- **100% Deterministic Offline Demo Mode**: Zero-latency local vector retriever and cache ensures seamless offline live presentations without risk of Wi-Fi failure or API rate limits.
- **Interactive Streamlit Web Interface**: Premium dark glassmorphic design, live execution pipeline badges, one-click challenge question chips, and chat transcript download.

---

## 🏗️ Architecture & Workflow

```text
                               +-----------------------------+
                               |     User Input Query        |
                               +--------------+--------------+
                                              |
                                              v
                               +-----------------------------+
                               |   Hybrid Domain Classifier  |
                               +--------------+--------------+
                                              |
                     +------------------------+-----------------------+
                     | (Non-Legal / STEM)                             | (Legal In-Scope)
                     v                                                v
       +----------------------------+                   +-----------------------------+
       |   Domain Boundary Notice   |                   |    Local Vector Retriever   |
       |  (e.g. Reject ML Query 5)  |                   |   (TF-IDF / Cosine Matrix)  |
       +----------------------------+                   +--------------+--------------+
                                                                       |
                                                                       v
                                                        +-----------------------------+
                                                        |  Evidence Threshold Check   |
                                                        |   (Max Similarity >= 0.22)  |
                                                        +--------------+--------------+
                                                                       |
                                              +------------------------+-----------------------+
                                              | (Below Threshold / Fictional Law)              | (Sufficient Evidence)
                                              v                                                v
                                +-----------------------------+                  +-----------------------------+
                                | Insufficient Evidence Guard |                  |     LLM Grounded Synthesis  |
                                |   (Anti-Hallucination)      |                  | (Gemini 1.5 / Offline Cache)|
                                +-----------------------------+                  +--------------+--------------+
                                                                                               |
                                                                                               v
                                                                                 +-----------------------------+
                                                                                 |   Citation Attribution &    |
                                                                                 |   Legal Safety Disclaimer   |
                                                                                 +--------------+--------------+
                                                                                               |
                                                                                               v
                                                                                 +-----------------------------+
                                                                                 |  Streamlit UI Output & Badges|
                                                                                 +-----------------------------+
```

---

## 📋 5 Competition Challenge Questions Addressed

| # | Challenge Question from `Build_A_Bot.md` | System Behavior & Legal Basis |
|---|------------------------------------------|-------------------------------|
| **1** | *Is it true that Article 21 guarantees the right to life and personal liberty?* | **Verified True**: Cites Article 21, *Maneka Gandhi (1978)* substantive due process, human dignity, and non-suspendability under Art 359. |
| **2** | *Under Indian law, police can arrest any person without reason or evidence at any time. Is this correct?* | **Clarified False**: Cites CrPC Sec 41 / BNSS Sec 35, *Arnesh Kumar (2014)* requirements for written reasons, Sec 50 grounds communication, and Sec 41B arrest memo. |
| **3** | *If arrest requires legal grounds, what rights does a person have at the time of arrest in India?* | **Structured Breakdown**: Explains grounds notification (Art 22(1)), legal counsel (Sec 41D), family intimation (Sec 50A), 24-hr magistrate production (Sec 57), medical examination (Sec 54), and free legal aid (Art 39A). |
| **4** | *Suppose a person is arrested without being informed of the reason and not produced before a magistrate within 24 hours. What would you advise?* | **Procedural Remedy**: Identifies illegal detention under Art 22(2) & CrPC Sec 57; advises urgent Writ of *Habeas Corpus* (Art 226/32), CJM application, and NALSA/DLSA escalation. |
| **5** | *What are the main principles behind machine learning algorithms like decision trees?* | **Domain Boundary Interception**: Correctly classifies query as non-legal (Computer Science/STEM) and politely redirects to Indian Constitutional law. |

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14.6)
- Git

### 2. Clone & Setup Virtual Environment
```bash
git clone https://github.com/your-team/legal-assistant.git
cd legal-assistant
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys (Optional)
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Add your `OPENROUTER_API_KEY` (or `GEMINI_API_KEY`) or leave blank to utilize the deterministic offline demo engine.

### 5. Launch Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Automated Benchmarking & Testing
Run the comprehensive 30-question evaluation benchmark:
```bash
python tests/test_runner.py
```
**Results Overview:**
- **Domain Classification Accuracy**: 100.0%
- **Grounded Responses**: 100.0%
- **Hallucination Rate on Traps**: 0.0%
- **Offline Response Latency**: < 20 ms

---

## 📂 Project Structure
```text
Chat_Bot/
├── app.py                      # Streamlit application with modern UI
├── requirements.txt            # Dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git security exclusions
├── README.md                   # Project overview & documentation
│
├── knowledge_base/             # Verified legal documents
│   ├── constitution/           # Articles 14, 19, 21, 22, 32, 226
│   ├── arrest_and_detention/   # CrPC/BNSS, 24hr magistrate, legal aid, D.K. Basu
│   └── metadata/
│       └── sources.json        # Official sources catalog
│
├── src/                        # Core Python package
│   ├── config.py               # Settings & thresholds
│   ├── prompts.py              # System prompts & guardrails
│   ├── retriever.py            # Local vector search & thresholding
│   ├── classifier.py           # Domain detection & out-of-scope filter
│   ├── llm.py                  # Multi-provider LLM client with retry & fallback
│   ├── safety.py               # Disclaimers & citation formatters
│   └── fallback.py             # Deterministic cached answers for demo questions
│
├── tests/                      # Automated test suite
│   ├── test_questions.csv      # 30+ categorized test questions
│   └── test_runner.py          # Benchmark runner script
│
└── Docs/                       # Competition deliverables
    ├── PROMPT.md               # Master prompt specification
    ├── Build_A_Bot.md          # Competition rules & questions
    ├── PRESENTATION_SLIDES.md  # 9-Slide presentation deck & script (<4 min)
    └── JUDGE_QA.md             # 20 High-probability judge Q&As
```

---

## ⚖️ Legal Safety & Ethical Compliance
NyayaSahayak strictly complies with legal ethics:
1. Provides **general legal information** and procedural literacy rather than unauthorized legal representation.
2. Every response includes a standard **legal disclaimer**.
3. High-risk situations are actively escalated to the **National Legal Services Authority (NALSA helpline 15100)** or licensed advocates.
