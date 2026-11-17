# ⚖️ ClauseCheck

**AI contract risk analysis assistant for non-lawyers**

Upload a contract and get a short summary of it, plus a clause-by-clause list of risky
or unclear provisions. Each one is highlighted in the text, explained in plain language,
and can be downloaded as a PDF report.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest%20%2B%20vitest-brightgreen)
![Status](https://img.shields.io/badge/status-MVP%20·%20Sprint%203-orange)

> [!WARNING]
> **This tool does not provide legal advice and does not replace a licensed attorney.**
> Flags and summaries are AI-generated starting points for your own review.

**Team:** Makhambet Y. (backend), Kopbergen A. (AI lead, Product Owner), Dinmukhamed Z. (UI/UX),
Altynbek M. (security, testing, integration), Manarbekuly A. (research, QA, Scrum Master).

## Table of contents

- [Features](#features)
- [What's new in Sprint 3](#whats-new-in-sprint-3)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Using the app](#using-the-app)
- [How it works](#how-it-works)
- [Limits and quotas](#limits-and-quotas)
- [API reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project structure](#project-structure)
- [Languages and themes](#languages-and-themes)
- [Privacy](#privacy)
- [Troubleshooting](#troubleshooting)
- [Limitations and roadmap](#limitations-and-roadmap)
- [Disclaimer](#disclaimer)

---

## Features

- 📄 **Upload or paste**: drag-and-drop or file picker (PDF, DOCX, TXT/MD), or plain-text paste.
  PDF text is cleaned up: hyphenated words are rejoined, line breaks inside sentences are removed,
  and page numbers and repeated headers or footers are dropped.
- 🧾 **Contract summary**: contract type, parties, a 2–3 sentence overview and up to 6 key terms
  (payment, duration, termination, liability, IP, and so on).
- 🤖 **AI risk analysis**: Gemini flags risky, unclear or unusually one-sided clauses and rates each
  one **High / Medium / Low** against a calibrated rubric, judged from the signer's point of view.
  Explanations are hedged and use everyday language. At most 12 flags are returned, most serious first.
- 🖍️ **Results view**: the original text with color-coded highlights, plus a side panel linked to
  them. Click a highlight to scroll to its explanation, or the other way round. Long excerpts can be
  expanded to their full text.
- 📥 **PDF report**: **Download PDF report** builds a print-ready report (summary, risk counts,
  every flag with its quote and explanation, disclaimer) and opens the browser's *Save as PDF* dialog.
- 🛡️ **Disclaimers**: a clear AI disclaimer at the top of the results, a privacy note before
  upload, and a persistent disclaimer on every screen.
- 🌍 **Three interface languages**: English, Русский, Қазақша. The AI's summary, explanations and
  error messages follow the selected language. Quoted clauses always stay verbatim.
- 🌗 **Light / dark theme**: follows your OS until you choose; your choice is remembered.
- 🚦 **Fair use**: per-user rate limits, a queue for concurrent analyses, and clear messages
  when the Gemini quota runs out.
- 🔒 **No persistence**: documents are processed in memory for the duration of the request only.

**Out of scope (intentionally):** accounts/auth, version comparison, editing/redlining,
document storage, automated decisions.

## What's new in Sprint 3

These are the Sprint 3 product items from the *SIS 12 Resource Management Report*,
plus fixes found in a code review.

| ID | Item | What was done |
| -- | ---- | ------------- |
| US6 | Contract summary | New `summary` object in the AI schema and prompt; summary card on the results screen and in the PDF report |
| US7 | Download report | Print-only report layout + **Download PDF report** button (works with Cyrillic and Kazakh text, no extra libraries) |
| I-05 | Calibrate Low level | Prompt rubric with criteria and examples for each risk level; harmless boilerplate is no longer flagged as Low |
| I-06 | Stronger result disclaimer | Disclaimer banner at the top of the results and in the PDF report |
| TD-3 | Layout-aware PDF extraction | Hyphen joins, line rejoining, page-number and repeated header/footer removal, a clear error for password-protected PDFs |
| TD-4 | Gemini quota handling, queue, per-user limits | Per-IP minute/day limits (429 + `Retry-After`), concurrency queue (503 when busy), a separate "AI quota reached" message |
| DEP | Deploy to a public URL | One-service `Dockerfile` (FastAPI also serves the built frontend), `render.yaml`, configurable CORS |
| DEP | Paid Gemini key and data settings | `.env.example` documents every setting and the free-tier data-use warning |
| REG | Regression run | 172 backend tests (pytest) + frontend tests (Vitest) |

**Fixes from the code review**

- The setup step `cp .env.example .env` failed because `.env.example` was git-ignored. The file is now in the repo.
- One analysis blocked the whole server (blocking Gemini calls inside an `async` route). It now runs in a worker thread.
- Retries were decided by searching error text for numbers like `"500"`. They now use the SDK's HTTP status code.
- Raw Gemini error text was shown to users. It now goes to the server log only, and users see a translated message.
- Uploads were fully read into memory before the size check. The read is now capped at 10 MB + 1 byte.
- The fallback model could be a preview or experimental model. Only stable models are chosen now, in a fixed order.
- The prompt allowed 12 flags while the code capped at 20. There is now one `MAX_FLAGS = 12`.
- Pasted text skipped the cleanup and minimum length that uploads get. Both now go through the same steps.
- Going home during an analysis still jumped to the results when they arrived. The request is now cancelled.
- Pasted text was lost after an error. The input now survives errors.
- Overlapping highlights were counted as "not found". They are now reported correctly.
- Characters whose lowercase form has a different length (e.g. `İ`) shifted the highlights. This is fixed.
- Dependencies now have upper version bounds, and there is a 150-second request timeout in the frontend.

**Hardening from the independent review**

- The rate limit could be bypassed with a fake `X-Forwarded-For` header. The proxy-added entry is used now, and the limiter's memory is capped.
- Gemini calls had no timeout. Every call is now time-limited, with a total deadline under the frontend timeout. Health and static routes no longer wait on worker threads.
- Quota errors were retried with backoff for about 30 s. They now fail fast, after one fallback attempt.
- Oversized request bodies are rejected while they stream in, and file uploads are rate-limited before parsing.
- `Retry-After` is now exposed through CORS, the retry hint is no longer shown twice, and the missing-key message no longer reveals server setup.
- Missing `/assets/*` files return 404 (no HTML served as JavaScript), and hashed assets are cached as immutable.
- The Docker image builds on Node 22 and runs as a non-root user.

## Tech stack

| Layer    | Technology                                                    |
| -------- | ------------------------------------------------------------- |
| Frontend | React 18 + Vite, plain CSS (no UI framework), Vitest          |
| Backend  | Python 3.10+ / FastAPI, pytest                                |
| LLM      | Google Gemini (`google-genai` SDK, JSON-schema output)        |
| Parsing  | `pypdf` (PDF), `python-docx` (DOCX)                           |
| Deploy   | Docker (one service), Render blueprint (`render.yaml`)         |
| Database | None, everything is in memory per request                     |

---

## Quick start

### Prerequisites

- **Python 3.10+** and **Node.js 18+**
- A **Gemini API key**, free at <https://aistudio.google.com/apikey> (see [Privacy](#privacy)
  before using real contracts)
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
> Never commit `.env`. It is listed in `.gitignore`. Only `.env.example`
> (with placeholder values) belongs in the repository.

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

Open <http://localhost:5173>. The Vite dev server proxies `/api` to the backend.

**Health check:** <http://localhost:8000/api/health> should return `{"status":"ok"}`.

---

## Configuration

All backend settings live in `backend/.env` (copy `backend/.env.example`).

| Variable                  | Default                                        | Meaning |
| ------------------------- | ---------------------------------------------- | ------- |
| `GEMINI_API_KEY`          | none (required)                                | Gemini API key |
| `GEMINI_MODEL`            | `gemini-3.6-flash`                             | Primary model; a stable fallback is found automatically if it is unavailable |
| `GEMINI_SEED`             | `42`                                           | Fixed seed (with temperature 0) for repeatable results |
| `RATE_LIMIT_PER_MINUTE`   | `5`                                            | Analyses per client per minute (`0` = off) |
| `RATE_LIMIT_PER_DAY`      | `50`                                           | Analyses per client per day (`0` = off) |
| `MAX_CONCURRENT_ANALYSES` | `2`                                            | Gemini calls running at once; extra requests wait in the queue |
| `QUEUE_TIMEOUT_SECONDS`   | `30`                                           | How long a request may wait for a slot before HTTP 503 |
| `GEMINI_TIMEOUT_SECONDS`  | `60`                                           | Timeout of a single Gemini call |
| `ANALYSIS_DEADLINE_SECONDS` | `110`                                        | Total time budget for all attempts plus the fallback model (stays under the frontend's 150 s timeout) |
| `TRUST_PROXY`             | `0`                                            | `1` = read the client IP from `X-Forwarded-For` (only behind a trusted proxy) |
| `TRUSTED_PROXY_HOPS`      | `1`                                            | Which `X-Forwarded-For` entry, counted from the end, is the real client (1 = the last, added by your proxy) |
| `MAX_TRACKED_CLIENTS`     | `10000`                                        | Memory cap of the rate limiter (least recently seen clients are dropped first) |
| `ALLOWED_ORIGINS`         | `http://localhost:5173,http://127.0.0.1:5173`  | CORS origins (comma-separated) |
| `PORT`                    | `8000`                                         | Port used by the Docker image |

Frontend (optional, build time): `VITE_API_BASE`. Set it only when the frontend and backend are
hosted separately, e.g. `VITE_API_BASE=https://api.example.com`. Leave it empty for the
single-service deployment.

---

## Using the app

1. **Paste** contract text or **upload** a PDF/DOCX/TXT using the chips under the input card,
   then press the circular **→** button.
2. Wait a few seconds while the analysis runs. Clicking the logo cancels it, and your input is kept.
3. The results screen shows the **disclaimer banner**, the **contract summary**, the risk counts,
   and two linked columns: click any **highlight** or **panel entry** to scroll the other column to it.
4. Press **Download PDF report**, then choose *Save as PDF* in the print dialog.
   The file name is suggested as `ClauseCheck-report-YYYY-MM-DD`.
5. Use **☀️/🌙** to switch the theme and **⚙️ Settings** to change the interface language.
6. No contract at hand? Click **See Example Analysis** to run the bundled sample
   (`samples/freelance-agreement.txt`, a freelance agreement with planted risky clauses).

---

## How it works

```
upload/paste → extract + clean → limits  → Gemini call      → validate + sort → render / PDF report
 (main.py)     (extraction.py)  (limits.py) (analysis.py +     (analysis.py)    (Results.jsx,
                                             prompts.py)                          PrintReport.jsx)
```

1. **Upload**: `POST /api/analyze` receives a multipart file *or* pasted text (`backend/main.py`).
   Uploads are read up to 10 MB; text is limited to 200k characters. Nothing is written to disk.
2. **Extract and clean**: `pypdf` / `python-docx` / direct decode (`backend/extraction.py`).
   PDF pages are cleaned up: hyphen joins, rejoined lines, page numbers and repeated headers or
   footers removed. Scanned, empty, or password-protected documents get a clear error.
3. **Limits**: the client's minute/day quota is checked and the request takes a slot in the
   analysis queue (`backend/limits.py`).
4. **LLM call**: the text is sent to Gemini with a system prompt (`backend/prompts.py`). The prompt
   asks for a summary, verbatim clause excerpts, a calibrated risk level and hedged explanations
   in the UI language. Output is **schema-constrained JSON**. Temporary errors are retried with
   exponential backoff, then one stable fallback model is tried.
5. **Validate**: Pydantic checks the schema. Duplicates are dropped (the most severe is kept), flags
   are sorted High → Medium → Low and then by position in the contract, and capped at 12.
6. **Render**: the frontend locates each excerpt in the original text (ignoring case and spacing,
   `frontend/src/lib/spans.js`) and highlights it. Excerpts that can't be located still appear in
   the panel. The same data feeds the print-only PDF report.

---

## Limits and quotas

| Situation                                   | HTTP | What the user sees |
| ------------------------------------------- | ---- | ------------------ |
| No input, text under 50 characters, unreadable/unsupported/encrypted file | 400 | Translated explanation |
| File over 10 MB or text over 200,000 characters | 413 | Translated explanation (oversized bodies are cut off before they are fully received) |
| More than `RATE_LIMIT_PER_MINUTE` / `RATE_LIMIT_PER_DAY` analyses | 429 + `Retry-After` | "Too many requests" + "try again in N s" |
| Gemini quota exhausted (no backoff; one fallback attempt) | 429 + `Retry-After` | "AI quota reached, try later" |
| All analysis slots busy for `QUEUE_TIMEOUT_SECONDS` | 503 + `Retry-After` | "Server is busy" + "try again in N s" |
| Missing `GEMINI_API_KEY` | 503 | "Service not configured yet" (the setup hint goes to the server log) |
| Any other AI failure | 502 | Generic translated message (details go to the server log only) |

**What counts against the rate limit:** file uploads are counted *before* parsing, so repeatedly
uploading heavy PDFs is limited too. Pasted text is counted once it passes validation. Requests with
no input, or with an oversized body, are free. Behind a proxy, the client IP is the
`X-Forwarded-For` entry your proxy added (`TRUSTED_PROXY_HOPS`), so a client can't fake an IP to
bypass the limit. Limits and the queue are in memory per server process, so run a single instance
(or move them to Redis) when scaling out.

---

## API reference

| Method | Route          | Body / query                                   | Response |
| ------ | -------------- | ---------------------------------------------- | -------- |
| `POST` | `/api/analyze` | multipart: `file` (PDF/DOCX/TXT/MD) **or** `text`; optional `lang` (`en` \| `ru` \| `kk`) | `{ full_text, summary, flags }` |
| `GET`  | `/api/sample`  | optional `?lang=en\|ru\|kk`                    | `{ text }` (demo contract) |
| `GET`  | `/api/config`  | none                                           | `{ max_file_mb, max_chars, max_flags }` |
| `GET`  | `/api/health`  | none                                           | `{ status: "ok" }` |

**Response of `/api/analyze`**

```json
{
  "full_text": "…",
  "summary": {
    "contract_type": "Freelance services agreement",
    "parties": ["Client", "Contractor"],
    "overview": "…",
    "key_terms": ["Payment within 60 days of invoice", "…"]
  },
  "flags": [
    { "clause_text": "…verbatim excerpt…", "risk_level": "High", "explanation": "…" }
  ]
}
```

Errors return `{ "detail": "..." }`, translated into the requested `lang` (see [Limits and quotas](#limits-and-quotas)).

**Example request**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "lang=en" \
  -F "text=The Client may terminate this Agreement at any time without payment for work already completed by the Contractor."
```

---

## Testing

```bash
# Backend: 172 regression tests (Gemini is mocked, no API quota used)
cd backend
pip install -r requirements-dev.txt
python -m pytest -q

# Frontend: highlight-matching tests, translation check, production build
cd frontend
npm test
npm run check:i18n
npm run build
```

The backend tests cover text extraction and PDF cleanup, deduplication and ordering, error
classification, translations (every message in en/ru/kk with matching placeholders), the rate
limiter and queue, and every API status code above.

---

## Deployment

The app deploys as **one service**: the `Dockerfile` builds the frontend, and FastAPI serves
`frontend/dist` next to the `/api` routes, so no CORS setup is needed.

**Render (blueprint)**

1. Push the repository to GitHub and choose **New → Blueprint** in Render; it reads `render.yaml`.
2. Set `GEMINI_API_KEY` in the service's environment (use a **paid** key for real documents).
3. Deploy; Render checks `/api/health`. `TRUST_PROXY=1` is preset so rate limits use the real client IP.

**Any Docker host**

```bash
docker build -t clausecheck .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key clausecheck
# open http://localhost:8000
```

---

## Project structure

```
RISK-analyzer/
├── Dockerfile           # one-service image: builds frontend, runs FastAPI
├── render.yaml          # Render blueprint
├── backend/
│   ├── main.py          # FastAPI app, routes, status codes, static frontend serving
│   ├── extraction.py    # PDF/DOCX/TXT → clean text (incl. PDF layout cleanup)
│   ├── limits.py        # per-client rate limiter + analysis queue
│   ├── analysis.py      # Gemini call, retries/fallback, validation, ordering
│   ├── prompts.py       # system prompt, risk rubric, JSON schema (summary + flags), MAX_FLAGS
│   ├── messages.py      # user-facing messages in en / ru / kk
│   ├── tests/           # pytest regression suite
│   ├── requirements.txt / requirements-dev.txt
│   └── .env.example     # all settings; copy to .env
├── frontend/
│   ├── vite.config.js   # dev proxy /api → :8000
│   ├── scripts/check-i18n.mjs
│   └── src/
│       ├── App.jsx      # screen flow, request cancelling, input state
│       ├── api.js       # fetch wrappers, timeout, VITE_API_BASE, Retry-After
│       ├── i18n/        # translations (en / ru / kk) + I18nContext
│       ├── theme/       # ThemeContext (light / dark)
│       ├── lib/spans.js # locate excerpts for highlighting (+ spans.test.js)
│       ├── components/  # Navbar, Hero, InputCard, LoadingState, Results, SummaryCard,
│       │                # HighlightedText, FlagPanel, PrintReport, modals, Disclaimer
│       └── styles/      # global.css, Hero.css, Results.css, Print.css
├── samples/             # demo contract with planted risky clauses
└── README.md
```

---

## Languages and themes

- **Language**: stored in `localStorage` (`clausecheck.lang`); on the first visit it is taken from the
  browser language. It is sent as `lang` with every request, and the backend uses it for the summary,
  the explanations and error messages. Quoted clauses always stay verbatim.
- **Theme**: stored as `clausecheck.theme`; colors are CSS variables in `frontend/src/styles/global.css`.
  The PDF report always uses a light, printer-friendly palette.

**Adding another language**

1. Add `{ code: 'xx', label: 'Native name' }` to `LANGUAGES` and a full copy of the `en` block in
   `frontend/src/i18n/translations.js`.
2. Add the code to `SUPPORTED_LANGS` / `LANGUAGE_NAMES` and a translation for every message in
   `backend/messages.py`.
3. Run `npm run check:i18n` (frontend) and `python -m pytest tests/test_messages.py` (backend).

---

## Privacy

ClauseCheck itself stores nothing: documents live in memory for the request only, and the PDF report
is generated in your browser. However, **the contract text is sent to the Google Gemini API**.
On the **free tier, Google may use submitted content to improve its products**. Use a paid key
(billing enabled) before analysing real client documents, and don't upload confidential contracts
until you have reviewed Google's API terms.

## Troubleshooting

| Problem                                   | Fix |
| ----------------------------------------- | --- |
| "Service not configured yet" (503)        | `GEMINI_API_KEY` is missing (the server log says so): create `backend/.env` from `.env.example`, set the key, restart the backend. |
| Frontend shows a network error            | Make sure the backend is running on port 8000 (`/api/health`). |
| "Too many requests" (429)                 | Wait for the time shown, or raise `RATE_LIMIT_PER_MINUTE` / `RATE_LIMIT_PER_DAY` for local testing. |
| "AI quota reached" (429)                  | The Gemini free-tier quota is used up; wait or switch to a paid key. |
| "Server is busy" (503)                    | Too many analyses at once; retry, or raise `MAX_CONCURRENT_ANALYSES`. |
| "No text found" for a PDF                 | The PDF is probably a scan (images only). OCR is not supported yet. Paste the text instead. |
| Password-protected PDF error              | Remove the password (re-save the PDF) and upload again. |
| PowerShell blocks `activate`              | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |
| Some flags have no inline highlight       | The model paraphrased the excerpt; the explanation is still in the side panel. |
| PDF report is blank or shows the app      | Use the **Download PDF report** button (not Ctrl+P from another screen) and choose *Save as PDF*. |

---

## Limitations and roadmap

**Current limitations**

- Single LLM call; documents over **200k characters** are rejected.
- Rate limits and the queue are in memory and per process (single-instance deployment).
- The PDF cleanup is heuristic: multi-column layouts and complex tables may still come out imperfect.
- The PDF report uses the browser's print dialog (*Save as PDF*) rather than a direct file download.
- Highlights require the model to reproduce clause text verbatim; unmatched flags appear only in the panel.
- The model can miss issues or flag imperfectly. Always confirm with a licensed attorney.

**Possible next steps**

- [ ] Chunking for long documents
- [ ] OCR for scanned PDFs
- [ ] Shared rate limits (Redis) for multi-instance deployments
- [ ] Multi-language contract support beyond the three UI languages
- [ ] Markdown/DOCX export of the analysis

---

## Disclaimer

This software is provided for informational purposes only and does **not** constitute
legal advice. It does not create an attorney–client relationship and is not a substitute
for advice from a qualified lawyer.
