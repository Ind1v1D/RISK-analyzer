# ClauseCheck — AI Contract Risk Analysis Assistant (MVP)

A first-pass contract review tool for non-lawyers: upload a contract (PDF,
DOCX, or pasted text) and get an AI-generated, clause-by-clause list of risky
or unclear provisions, highlighted inline and explained in plain language.

> **This tool does not provide legal advice and does not replace a licensed
> attorney.** Flags are AI-generated starting points for your own review.

Built for a university IT project management course deliverable.

---

## Features (MVP scope)

- **Upload or paste** — drag-and-drop / file picker (PDF, DOCX, TXT) or plain-text paste
- **AI analysis** — Gemini reviews the contract, flags risky/unclear/unusually
  unfavorable clauses, classifies each **High / Medium / Low**, and explains
  why in non-legal language (hedged, never claims certainty)
- **Results view** — original contract text with color-coded highlights plus a
  scroll-linked side panel with a plain-language explanation per flag
- **Persistent disclaimer** on every screen
- **No persistence** — documents are processed in memory for the request only

**Out of scope (intentionally):** accounts/auth, version comparison, editing/
redlining, document storage, automated decisions.

## Tech stack

| Layer     | Tech                                                        |
| --------- | ----------------------------------------------------------- |
| Frontend  | React 18 + Vite, plain CSS (no UI framework)                 |
| Backend   | Python 3.10+ / FastAPI                                      |
| LLM       | Google Gemini (`google-genai` SDK, JSON-schema output)      |
| Parsing   | `pypdf` (PDF), `python-docx` (DOCX)                          |
| Database  | none — in-memory per request                                |

---

## Setup

### Prerequisites

- **Python 3.10+** and **Node.js 18+**
- A **Gemini API key** — free at <https://aistudio.google.com/apikey>

### 1. Backend

```powershell
cd contract-risk-assistant\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Add your API key
Copy-Item .env.example .env
# then edit .env and set GEMINI_API_KEY=your-real-key
```

### 2. Frontend

```powershell
cd contract-risk-assistant\frontend
npm install
```

---

## Running locally

Two terminals:

**Terminal 1 — backend** (port 8000):

```powershell
cd contract-risk-assistant\backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — frontend** (port 5173):

```powershell
cd contract-risk-assistant\frontend
npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api` to the
backend, so no CORS configuration is needed in development.

Quick check: <http://localhost:8000/api/health> should return `{"status":"ok"}`.

---

## Using the app

1. **Paste** contract text or **upload** a PDF/DOCX/TXT using the chips under
   the input card, then hit the circular **→** button.
2. Wait a few seconds for the analysis (loading state shows progress text).
3. On the results screen, click any **highlight** or **panel entry** — the
   other column scrolls to the matching item.
4. Try **See Example Analysis** to run the bundled sample
   (`samples/freelance-agreement.txt`, a freelance agreement with planted
   risky clauses) — useful for demos.

---

## The analysis pipeline

Comments in the code mark each step; here's the flow end-to-end:

```
upload/paste  →  extract text  →  Gemini call  →  validate JSON  →  render
 (main.py)      (extraction.py)   (analysis.py +   (analysis.py)     (App.jsx →
                                   prompts.py)                       HighlightedText.jsx)
```

1. **Upload** — `POST /api/analyze` receives multipart file *or* pasted text
   (`backend/main.py`). 10 MB / 200k-character limits; nothing is written to disk.
2. **Extract** — `pypdf` / `python-docx` / direct decode, then whitespace cleanup
   (`backend/extraction.py`). Scanned/empty documents get a friendly error.
3. **LLM call** — text is sent to Gemini with a system prompt demanding verbatim
   clause excerpts, risk levels, hedged plain-language explanations, and a
   "don't over-flag boilerplate" rule (`backend/prompts.py`).
   Output is **schema-constrained JSON**, so parsing never depends on luck.
4. **Parse/validate** — Pydantic validates the schema; duplicates are dropped
   and results capped at 20 flags (`backend/analysis.py`).
5. **Render** — the frontend locates each flagged excerpt in the original text
   (case/whitespace-insensitive match), wraps it in a color-coded `<mark>`, and
   lists explanations in the side panel (`frontend/src/lib/spans.js`). Excerpts
   that can't be located still appear in the panel without an inline highlight.

---

## API

| Method | Route            | Body                                       | Response |
| ------ | ---------------- | ------------------------------------------ | -------- |
| `POST` | `/api/analyze`   | multipart: `file` (PDF/DOCX/TXT) **or** `text` | `{ full_text, flags: [{ clause_text, risk_level, explanation }] }` |
| `GET`  | `/api/sample`    | —                                          | `{ text }` (demo contract) |
| `GET`  | `/api/health`    | —                                          | `{ status: "ok" }` |

Errors return `{ "detail": "..." }` with a user-readable message.

---

## Project structure

```
contract-risk-assistant/
├── backend/
│   ├── main.py          # FastAPI app + routes (pipeline steps 1 & 5)
│   ├── extraction.py    # PDF/DOCX/TXT → plain text (step 2)
│   ├── analysis.py      # Gemini call + validation (steps 3-4)
│   ├── prompts.py       # System prompt + JSON output schema
│   ├── requirements.txt
│   └── .env.example     # copy to .env, add GEMINI_API_KEY
├── frontend/
│   ├── index.html       # fonts (Montserrat + Inter)
│   ├── vite.config.js   # dev proxy /api → :8000
│   └── src/
│       ├── App.jsx      # screen flow: landing → loading → results
│       ├── api.js       # fetch wrappers
│       ├── lib/spans.js # locate flagged clauses for highlighting
│       ├── components/  # Navbar, Hero, InputCard, LoadingState,
│       │                # Results, HighlightedText, FlagPanel, …
│       └── styles/      # global.css, Hero.css, Results.css
├── samples/             # demo contract with planted risky clauses
└── README.md
```

---

## Limitations & possible extensions

- Single LLM call; documents over **200k characters** are rejected (chunking
  is the natural next step).
- No document persistence, accounts, or contract editing — by design (MSSVP scope).
- Highlights require the model to reproduce clause text; unmatched flags still
  show in the panel.
- The model can miss issues or flag imperfectly — always confirm with a
  licensed attorney.

## Disclaimer

This software is provided for informational purposes only and does **not**
constitute legal advice. It does not create an attorney–client relationship
and is not a substitute for advice from a qualified lawyer.
