# ⚖️ AI Justice Department Assistant

An AI chatbot and legal knowledge retrieval system that helps citizens find and understand Indian statutory laws, legal rights, and procedural remedies quickly using **Retrieval-Augmented Generation (RAG)**.

Designed and developed for academic coursework at **Lovely Professional University (LPU)**.

---

## 🌟 Key Features

1. **RAG-Driven Indian Statutory Retrieval:**
   - Grounded in official Indian legislation:
     - **Bharatiya Nyaya Sanhita (BNS 2023)** & **Indian Penal Code (IPC 1860)**
     - **Bharatiya Nagarik Suraksha Sanhita (BNSS 2023)** & **Code of Criminal Procedure (CrPC 1973)**
     - **Constitution of India** (Fundamental Rights: Articles 14, 19, 21, 22, 32, 39A)
     - **Consumer Protection Act (2019)**
     - **Right to Information (RTI) Act (2005)**
     - **Information Technology Act (2000)** (Cybercrime provisions)
     - **Protection of Women from Domestic Violence Act (2005)**

2. **BNS ⇄ IPC / CrPC Cross-Reference Engine:**
   - Instant conversion between colonial-era sections (e.g. IPC Section 420) and modernized reformed codes (BNS Section 318), highlighting changes in bail eligibility and punishments.

3. **Verifiable Grounding & Zero Hallucination:**
   - Every answer is accompanied by an exact statutory citation card specifying Section, Act, Cognizable/Non-Cognizable status, Bailable status, and statutory punishments.

4. **Actionable Step-by-Step Remedies:**
   - Gives citizens practical next steps (e.g. how to file a Zero-FIR, report on the 1930 Cyber Helpline, submit an e-Daakhil consumer petition, or request free legal aid from NALSA).

5. **Multi-Interface Access:**
   - **Modern Web Dashboard** with interactive legal assistant, BNS code converter, and Law Library Explorer.
   - **Interactive Terminal CLI** for console-based querying.
   - **FastAPI REST API** for integration with external portals or mobile apps.

---

## 📁 Project Architecture

```
focused-babbage/
├── PROJECT_REPORT.md        # Comprehensive Academic Project Report (LPU Format)
├── main.py                  # FastAPI server & route handlers
├── cli.py                   # Interactive Command Line Interface
├── core/
│   ├── __init__.py
│   └── rag_engine.py        # Dense TF-IDF vectorizer, BM25 booster & LLM synthesizer
├── data/
│   └── statutes.json        # Curated Indian legal statutes & metadata
├── static/
│   ├── app.js               # Frontend chat logic, converter & library rendering
│   └── styles.css           # Modern judicial-themed UI styling
├── templates/
│   └── index.html           # Responsive web portal template
├── tests/
│   └── test_rag.py          # Automated unit test suite
└── README.md                # Project documentation
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Environment Setup
Python 3.10+ (tested on Python 3.14).

Create and activate the virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic requests jinja2 numpy scikit-learn anthropic
```

### 2. Launch the Web Application
Start the local server:
```bash
.venv/bin/python main.py
```
Open your browser and navigate to:
```
http://localhost:8000
```

### 3. Run the Command Line Interface (CLI)
For interactive terminal usage:
```bash
.venv/bin/python cli.py
```

### 4. Run Automated Tests
```bash
.venv/bin/python -m unittest tests/test_rag.py
```

---

## 🔌 REST API Endpoints

- `GET /` — Web Portal Interface
- `POST /api/chat` — Accepts `{ "query": "string" }` and returns grounded legal answer, citations, and follow-ups.
- `GET /api/convert?code=420` — Converts old IPC/CrPC section into current BNS/BNSS code.
- `GET /api/search?q=arrest` — Semantic vector search across all indexed statutes.
- `GET /api/statutes` — Retrieves all indexed statutes with categories and metadata.
- `GET /api/health` — System status and configuration check.

---

## 🚨 Official Citizen Helplines

- **National Cyber Crime Helpline:** 1930 ([cybercrime.gov.in](https://cybercrime.gov.in))
- **NALSA Free Legal Aid:** 15100 (Toll-Free, 24/7)
- **National Consumer Helpline:** 1915 ([consumerhelpline.gov.in](https://consumerhelpline.gov.in))
- **National Emergency (Police/Fire/Ambulance):** 112
- **Women in Distress Helpline:** 181 / 1091

---

## 📜 Disclaimer
*This project is designed for academic evaluation, legal literacy, and educational awareness under Article 39A of the Constitution of India. It does not constitute formal legal counsel or replace a licensed advocate.*
