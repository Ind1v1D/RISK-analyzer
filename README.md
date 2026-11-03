# ⚖️ ClauseCheck

**AI contract risk analysis assistant for non-lawyers**

Upload a contract, get a clause-by-clause list of risky or unclear provisions,
highlighted inline and explained in plain language.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)
![Status](https://img.shields.io/badge/status-MVP-orange)

</div>

> [!WARNING]
> **This tool does not provide legal advice and does not replace a licensed attorney.**
> Flags are AI-generated starting points for your own review.

<!-- Add a screenshot or GIF of the results screen here, e.g.:
![ClauseCheck results screen](docs/screenshot-results.png)
-->

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Using the app](#using-the-app)
- [How it works](#how-it-works)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Privacy](#privacy)
- [Troubleshooting](#troubleshooting)
- [Limitations and roadmap](#limitations-and-roadmap)
- [Disclaimer](#disclaimer)

---

## Features

- 📄 **Upload or paste**: drag-and-drop or file picker (PDF, DOCX, TXT), or plain-text paste.
- 🤖 **AI analysis**: Gemini reviews the contract, flags risky, unclear, or unusually
  unfavorable clauses, classifies each as **High / Medium / Low**, and explains why in
  non-legal language (hedged, never claims certainty).
- 🖍️ **Results view**: the original text with color-coded highlights, plus a scroll-linked
  side panel with a plain-language explanation for every flag.
- 🌍 **Three interface languages**: English, Русский, Қазақша. Switch in **Settings** (⚙️ in the navbar).
  The AI's explanations and the error messages are written in the selected language too.
- 🌗 **Light / dark theme**: one-click toggle (☀️/🌙 in the navbar). Follows your OS until you choose;
  your choice is remembered.
- 🛡️ **Persistent disclaimer** on every screen.
- 🔒 **No persistence**: documents are processed in memory for the duration of the request only.

**Out of scope (intentionally):** accounts/auth, version comparison, editing/redlining,
document storage, automated decisions.

## Tech stack

| Layer    | Technology                                             |
| -------- | ------------------------------------------------------ |
| Frontend | React 18 + Vite, plain CSS (no UI framework)           |
| Backend  | Python 3.10+ / FastAPI                                 |
| LLM      | Google Gemini (`google-genai` SDK, JSON-schema output) |
| Parsing  | `pypdf` (PDF), `python-docx` (DOCX)                    |
| Database | None, everything is in memory per request              |

---

## Quick start

### Prerequisites

- **Python 3.10+** and **Node.js 18+**
- A **Gemini API key**, free at <https://aistudio.google.com/apikey>
- **Git**

### 1. Clone the repository

```bash
git clone https://github.com/Ind1v1D/RISK-analyzer.git
cd RISK-analyzer
```

### 2. Set up the backend

<details open>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

</details>

Then open `backend/.env` and set your key:

```env
GEMINI_API_KEY=your-real-key
```

> [!IMPORTANT]
> Never commit `.env`. It is already listed in `.gitignore`. Only `.env.example`
> (with a placeholder value) belongs in the repository.

### 3. Set up the frontend

```bash
cd frontend
npm install
```

### 4. Run locally

You need two terminals.

**Terminal 1: backend** (port 8000)

```bash
cd backend
# activate the virtual environment first (see step 2)
uvicorn main:app --reload --port 8000
```

**Terminal 2: frontend** (port 5173)

```bash
cd frontend
npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api` to the backend,
so no CORS configuration is needed in development.

**Health check:** <http://localhost:8000/api/health> should return `{"status":"ok"}`.

---

## Using the app

1. **Paste** contract text or **upload** a PDF/DOCX/TXT using the chips under the input card,
   then press the circular **→** button.
2. Wait a few seconds while the analysis runs (the loading screen shows progress text).
3. On the results screen, click any **highlight** or **panel entry**. The other column
   scrolls to the matching item.
4. Use the **☀️/🌙** button to switch between light and dark theme, and **⚙️ Settings** to change the
   interface language (English, Русский, Қазақша). Both choices are saved in your browser.
5. No contract at hand? Click **See Example Analysis** to run the bundled sample
   (`samples/freelance-agreement.txt`, a freelance agreement with planted risky clauses).
   Handy for demos.

---

## How it works

```
upload/paste  →  extract text  →  Gemini call  →  validate JSON  →  render
 (main.py)      (extraction.py)   (analysis.py +   (analysis.py)     (App.jsx →
                                   prompts.py)                       HighlightedText.jsx)
```

1. **Upload**: `POST /api/analyze` receives a multipart file *or* pasted text
   (`backend/main.py`). Limits: 10 MB and 200k characters. Nothing is written to disk.
2. **Extract**: `pypdf` / `python-docx` / direct decode, then whitespace cleanup
   (`backend/extraction.py`). Scanned or empty documents get a friendly error.
3. **LLM call**: the text is sent to Gemini with a system prompt that demands verbatim
   clause excerpts, risk levels, hedged plain-language explanations, and a
   "don't over-flag boilerplate" rule (`backend/prompts.py`). Output is
   **schema-constrained JSON**, so parsing never depends on luck.
4. **Validate**: Pydantic checks the schema, duplicates are dropped, and results are
   capped at 20 flags (`backend/analysis.py`).
5. **Render**: the frontend locates each flagged excerpt in the original text
   (case- and whitespace-insensitive), wraps it in a color-coded `<mark>`, and lists
   explanations in the side panel (`frontend/src/lib/spans.js`). Excerpts that cannot be
   located still appear in the panel, just without an inline highlight.

---

## API reference

| Method | Route          | Body                                           | Response                                                           |
| ------ | -------------- | ---------------------------------------------- | ------------------------------------------------------------------ |
| `POST` | `/api/analyze` | multipart: `file` (PDF/DOCX/TXT) **or** `text`, optional `lang` (`en` \| `ru` \| `kk`, default `en`) | `{ full_text, flags: [{ clause_text, risk_level, explanation }] }` |
| `GET`  | `/api/sample`  | optional query `?lang=en\|ru\|kk`              | `{ text }` (demo contract)                                         |
| `GET`  | `/api/health`  | none                                           | `{ status: "ok" }`                                                 |

Errors return `{ "detail": "..." }` with a user-readable message in the requested `lang`.

**Example request**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "text=The Client may terminate at any time without payment for work completed."
```

---

## Project structure

```
RISK-analyzer/
├── backend/
│   ├── main.py          # FastAPI app + routes (pipeline steps 1 & 5)
│   ├── extraction.py    # PDF/DOCX/TXT → plain text (step 2)
│   ├── analysis.py      # Gemini call + validation (steps 3-4)
│   ├── prompts.py       # System prompt (+ output-language rule) + JSON output schema
│   ├── messages.py      # User-facing error messages in en / ru / kk
│   ├── requirements.txt
│   └── .env.example     # copy to .env, add GEMINI_API_KEY
├── frontend/
│   ├── index.html       # fonts (Montserrat + Inter)
│   ├── vite.config.js   # dev proxy /api → :8000
│   ├── scripts/check-i18n.mjs  # verifies all languages have the same keys
│   └── src/
│       ├── App.jsx      # screen flow: landing → loading → results
│       ├── api.js       # fetch wrappers (send the UI language to the backend)
│       ├── i18n/        # translations.js (en / ru / kk) + I18nContext (t(), setLang)
│       ├── theme/       # ThemeContext (light / dark)
│       ├── lib/spans.js # locate flagged clauses for highlighting
│       ├── components/  # Navbar, Hero, InputCard, LoadingState,
│       │                # Results, HighlightedText, FlagPanel,
│       │                # SettingsModal, HowItWorksModal, …
│       └── styles/      # global.css, Hero.css, Results.css
├── samples/             # demo contract with planted risky clauses
└── README.md
```

---

## Languages and themes

- **Language**: stored in `localStorage` (`clausecheck.lang`); on first visit it is taken from the browser
  language (Russian / Kazakh / otherwise English). The frontend sends it as `lang` with every request,
  and the backend uses it for the Gemini prompt (explanations only; the quoted clause text always stays
  verbatim) and for error messages.
- **Theme**: stored as `clausecheck.theme`; colors are CSS variables in `frontend/src/styles/global.css`
  (`:root` for light, `:root[data-theme='dark']` for dark).

**Adding another language**

1. Add `{ code: 'xx', label: 'Native name' }` to `LANGUAGES` and a full copy of the `en` block to
   `frontend/src/i18n/translations.js`.
2. Add the code to `SUPPORTED_LANGS` / `LANGUAGE_NAMES` and a translation for each message in
   `backend/messages.py`.
3. Run `npm run check:i18n` in `frontend/` to make sure no key is missing.

---

## Privacy

ClauseCheck itself stores nothing: documents live in memory for the request only.
However, **the contract text is sent to the Google Gemini API** for analysis.
Do not upload confidential or sensitive contracts unless you have reviewed Google's
API terms and data-handling policy for your key type (free vs. paid).

## Troubleshooting

| Problem                                   | Fix                                                                                       |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| `GEMINI_API_KEY` errors / 401 / 403       | Check that `backend/.env` exists and contains a valid key, then restart the backend.      |
| Frontend shows a network error            | Make sure the backend is running on port 8000 (`/api/health`).                            |
| "No text found" for a PDF                 | The PDF is probably a scan (images only). OCR is not supported yet.                       |
| PowerShell blocks `activate`              | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again.           |
| Some flags have no inline highlight       | The model paraphrased the excerpt. The explanation is still shown in the side panel.      |

---

## Limitations and roadmap

**Current limitations**

- Single LLM call; documents over **200k characters** are rejected.
- No document persistence, accounts, or contract editing, by design (MVP scope).
- Highlights require the model to reproduce clause text verbatim; unmatched flags appear only in the panel.
- The model can miss issues or flag imperfectly. Always confirm with a licensed attorney.

**Possible next steps**

- [ ] Chunking for long documents
- [ ] OCR for scanned PDFs
- [ ] Production deployment (frontend on Vercel/Netlify, backend on Render/Railway)
- [ ] Multi-language contract support
- [ ] Export of the analysis (PDF/Markdown)

---

## Disclaimer

This software is provided for informational purposes only and does **not** constitute
legal advice. It does not create an attorney–client relationship and is not a substitute
for advice from a qualified lawyer.

<!-- Optional: add a LICENSE file and mention it here, e.g. "Released under the MIT License." -->
