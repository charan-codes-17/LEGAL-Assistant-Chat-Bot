# BUILD-A-BOT Competition Presentation & Demo Deck (< 4 Minutes)
**Project Title**: LUMA — Grounded Indian Legal Information Assistant  
**Theme**: Legal Assistant  
**Event**: BUILD-A-BOT (Data Intelligence Club, Dept. of AI, Thiagarajar College of Engineering)  
**Target Video Duration**: 3 minutes 45 seconds  

---

## Slide 1: Title & Problem Statement
- **Visual Suggestion**: App header with scales of justice icon, team name, and tagline: *"Democratizing Legal Awareness with Hallucination-Free Grounded AI"*.
- **Key Points**:
  - Citizens face severe information asymmetry when interacting with police or criminal justice procedures.
  - LLMs frequently hallucinate legal sections, invent fictional precedents, and give dangerous unauthorized advice.
  - **Our Solution**: A strictly grounded, RAG-driven Indian Legal Assistant with zero-tolerance for hallucination.
- **Speaker Script (25s)**:
  > *"Good day respected judges! In India, millions of citizens are unaware of their fundamental rights during police interactions, such as mandatory 24-hour magistrate production or free legal aid. While general LLMs tend to invent non-existent laws and give risky advice, our team built **LUMA**—a competition-ready, grounded legal assistant designed to provide accurate, verified legal information backed by official statutes and Supreme Court precedents."*

---

## Slide 2: Strategic Scope & Narrow Domain
- **Visual Suggestion**: Infographic showing the focused domain: Constitution (Arts 14, 19, 21, 22, 32, 226) & Arrest Safeguards (CrPC/BNSS, D.K. Basu).
- **Key Points**:
  - Narrowed domain to ensure 100% verified factual coverage.
  - Covers Articles 14, 19, 21 (Life & Liberty), 22 (Arrest/Detention), 32/226 (Habeas Corpus), and 39A (Free Legal Aid).
  - Integrates CrPC Sec 41, 50, 57, 167 and landmark *D.K. Basu* guidelines.
- **Speaker Script (25s)**:
  > *"Rather than building an unreliable bot covering the vast expanse of all laws, we intentionally scoped our knowledge base to the most critical area: **Constitutional Fundamental Rights and Arrest/Detention Safeguards**. Every document in our knowledge base is curated directly from the Legislative Department, India Code, and Supreme Court records."*

---

## Slide 3: System Architecture & Workflow Pipeline
- **Visual Suggestion**: Clean pipeline diagram: *User Query -> Domain Classifier -> Vector Retriever (Threshold Check) -> LLM Synthesis -> Citation Verification & Legal Disclaimer -> Final Response*.
- **Key Points**:
  - Multi-stage pipeline ensuring strict safety boundaries.
  - Real-time Domain Classifier to reject out-of-scope queries (e.g., ML algorithms).
  - Sublinear TF-IDF + Cosine similarity vector index with strict evidence thresholding.
  - Multi-provider LLM support with deterministic offline demo cache fallback.
- **Speaker Script (30s)**:
  > *"Here is our architecture: When a query arrives, our Domain Classifier first detects if it is legal or out-of-scope. Next, our hybrid vector retriever extracts relevant provisions from our local indexed knowledge base. If similarity falls below our evidence threshold, the bot refuses to guess. If sufficient, the context is synthesized with strict citations, safety disclaimers, and rendered in our Streamlit UI."*

---

## Slide 4: Live Demo — Challenge Questions 1 & 2
- **Visual Suggestion**: Screen recording / live split-screen showing Question 1 (Article 21 verification) and Question 2 (Debunking arbitrary police arrest).
- **Key Points**:
  - **Q1**: Confirms Article 21 guarantees right to life & personal liberty, citing *Maneka Gandhi (1978)* and non-suspendability under Art 359.
  - **Q2**: Rebuts the misconception that police can arrest without reason, citing CrPC Sec 41, Sec 50, and *Arnesh Kumar (2014)*.
- **Speaker Script (30s)**:
  > *"Let's test the competition challenge questions! In Question 1, the user asks if Article 21 guarantees right to life. LUMA confirms with the exact constitutional text, citing Maneka Gandhi. In Question 2, it debunks the myth that police can arrest without reasons, citing CrPC Section 41 and the Arnesh Kumar ruling."*

---

## Slide 5: Live Demo — Challenge Questions 3 & 4
- **Visual Suggestion**: Live UI showing structured breakdown of arrest rights (Q3) and procedural remedies for illegal detention (Q4).
- **Key Points**:
  - **Q3**: Lists 6 core rights (Grounds, Legal Counsel, Family Intimation, 24-hr Magistrate, Medical Exam, Legal Aid).
  - **Q4**: Identifies unconstitutional detention past 24 hours, details Writs of *Habeas Corpus* (Art 32/226), and escalates to DLSA.
- **Speaker Script (30s)**:
  > *"For Question 3, the bot structures all 6 statutory arrest rights including D.K. Basu inspection memos. In Question 4, when presented with a scenario where someone is detained over 24 hours without a magistrate, the assistant explains the constitutional breach under Article 22(2) and CrPC Section 57, and details immediate Habeas Corpus remedies before the High Court."*

---

## Slide 6: Out-of-Domain Filter & Hallucination Prevention (Q5)
- **Visual Suggestion**: UI showing Question 5 ("Decision trees in machine learning") being politely rejected with domain boundary badge, and hallucination trap ("Article 99A arrest robots") returning insufficient evidence.
- **Key Points**:
  - **Q5 Out-of-Domain**: Accurately classifies non-legal queries and redirects users.
  - **Hallucination Trap**: Rejects queries with non-existent articles (Art 99A) or fictional acts.
  - **Citation Verification**: Every fact links directly to verified source cards.
- **Speaker Script (25s)**:
  > *"For Question 5 on Machine Learning Decision Trees, our domain classifier instantly intercepts the query and politely clarifies its legal boundaries without consuming LLM generation tokens. When probed with trick questions about fictional laws like 'Article 99A arrest robots', the evidence threshold ensures the bot refuses rather than hallucinating."*

---

## Slide 7: Resilience & Offline Fallback Architecture
- **Visual Suggestion**: Diagram showing API failure recovery / toggle for 100% deterministic offline demo mode.
- **Key Points**:
  - Multi-tier LLM engine (Google Gemini -> OpenRouter [Llama 3.3 / GPT-4o-mini] -> Deterministic Offline Cache).
  - Built-in TF-IDF Vector Space runs locally without internet or GPU requirements.
  - 100% live presentation reliability.
- **Speaker Script (25s)**:
  > *"Competition presentations often suffer from Wi-Fi drops or API rate limits. LUMA is engineered with a multi-tiered resilience engine. It runs smoothly with Gemini API, and instantly falls back to a deterministic offline cache and local vector engine if connectivity fails, ensuring zero downtime during live evaluation."*

---

## Slide 8: Evaluation & Benchmark Results
- **Visual Suggestion**: Benchmark metrics card showing 100% domain accuracy, 0 hallucinations, and sub-100ms offline latency across 30 test cases.
- **Key Points**:
  - 30 Categorized test cases (Constitutional facts, arrest rights, procedural advice, out-of-domain, adversarial jailbreaks).
  - 100% Groundedness on verified sources.
  - Instant response time with structured citation cards and chat export.
- **Speaker Script (25s)**:
  > *"We evaluated our system against an automated 30-question benchmark covering constitutional facts, adversarial jailbreaks, and trick questions. The system achieved 100% domain accuracy, 0 hallucinations on trap queries, and sub-100ms latency in offline demo mode."*

---

## Slide 9: Conclusion & Future Scope
- **Visual Suggestion**: Summary card with GitHub repo QR code, key strengths, and roadmap (Multilingual vernacular support, BNS/BNSS statutory cross-mapping).
- **Key Points**:
  - Complete, robust, competition-ready legal prototype built within the 20-hour limit.
  - Transparent legal disclaimers and verified citation cards.
  - Future roadmap: Expansion to regional Indian languages (Tamil, Hindi) and voice interface for rural citizens.
- **Speaker Script (20s)**:
  > *"In summary, LUMA is a reliable, grounded, and ethically safeguarded legal assistant ready for real-world impact and competition evaluation. Thank you, and we welcome your questions!"*
