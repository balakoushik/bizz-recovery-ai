# Bizz Recovery AI

**AI-Powered Business & Project Risk Prediction, Prevention and Recovery Platform**

A complete, locally-running Flask application that identifies business/project
risks, predicts future risk with a trained ML model, generates recovery plans,
runs What-If simulations, and answers questions through a built-in AI assistant
— all without requiring any paid API.

---

## 1. Requirements

- Python 3.10+
- pip

## 2. Setup

```bash
cd bizz-recovery-ai

# (recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# (optional) configure environment
cp .env.example .env
```

You do **not** need to edit `.env` to run the app — it works fully offline
out of the box using **Local Intelligence Mode** for the AI Assistant.

## 3. Run

```bash
python app.py
```

The app creates `bizz_recovery.db` automatically, seeds it with 4 realistic
sample projects and their detected risks, and opens your browser at:

```
http://127.0.0.1:5000
```

## 4. What you get

- **Dashboard** — business/project health, risk counts, 6 live charts, early warnings
- **Projects** — create/view/delete projects with full risk-relevant fields
- **Risk Analysis** — rule-based risk detection engine across 12 risk categories
- **Predictions** — RandomForestClassifier (scikit-learn) trained on synthetic
  data, with an honest confidence/accuracy disclosure and automatic fallback
  to the rule engine if ML is unavailable
- **Recovery Plans** — full 14-section AI-generated recovery plan per project
- **What-If Simulation** — adjust budget, team size, progress, security
  incidents, etc. and see BEFORE vs AFTER health/risk impact with an explanation
- **AI Assistant** — chat interface answering questions using your real
  project data (Local Intelligence Mode by default; optionally plug in an
  Anthropic API key for richer answers — see below)
- **Reports** — print-friendly / "Save as PDF" business risk report per project
- **REST API** — `/api/projects`, `/api/risks`, `/api/dashboard`,
  `/api/analyze-risk`, `/api/predict-risk`, `/api/recovery-plan`,
  `/api/what-if`, `/api/ai-assistant`

## 5. Optional external LLM mode

By default the AI Assistant uses **Local Intelligence Mode** — a rule-based
engine that reasons over your actual stored project/risk data with no
external calls at all.

To optionally let it use Claude for richer natural-language answers (still
grounded only in your real data), set this in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Restart the app. If the key is missing, invalid, or the call fails for any
reason, the assistant automatically and silently falls back to Local
Intelligence Mode — the app never breaks because of a missing/failed API key.

## 6. Project structure

```
bizz-recovery-ai/
├── app.py                  Flask app factory & entry point
├── config.py                Configuration
├── requirements.txt
├── .env.example
├── database/
│   └── database.py          SQLAlchemy instance + seeding
├── models/                  project.py, risk.py, recovery.py, user.py
├── services/                risk_engine, prediction_engine, recovery_engine,
│                             ai_engine, analytics_engine
├── routes/                  dashboard, projects, risks, recovery, pages, api
├── templates/                all HTML pages (Jinja2 + Bootstrap 5)
├── static/
│   ├── css/style.css
│   └── js/dashboard.js, risk.js, what_if.js
└── data/sample_data.csv     reference copy of the seeded sample projects
```

## 7. Notes on the ML model

The prediction module is honest about its limitations: since no
organization-specific historical outcome data exists, it trains a
`RandomForestClassifier` on **synthetically generated** data patterned after
common project-risk indicators (budget utilization, schedule gap, team size,
issue backlog, security incidents, customer satisfaction, infrastructure
utilization, dependency delays). Its holdout accuracy is reported transparently
on the Predictions page, and it is explicitly labeled as decision-support,
not ground truth. If scikit-learn/numpy fail to load or train for any reason,
the app automatically falls back to a transparent weighted rule-based heuristic
so the application never crashes.
