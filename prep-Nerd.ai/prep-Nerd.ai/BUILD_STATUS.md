# Build status

Completed in this build:

- Streamlit dashboard with seven integrated modules and warm, light visual styling.
- Official `google-genai` service wrapper with centralized model configuration, clear missing-key errors, JSON parsing, and no fake fallback output.
- SQLite persistence for sources, notes/summaries, flashcards, and mistakes.
- Supported TXT/PDF/Markdown/PPTX/DOCX extraction; `.ppt` has a transparent limitation.
- URL fetching with public-destination SSRF checks, timeout, size limit, and redirect validation.
- Quiz validation, 5/10/15/20/25 count enforcement, deterministic scoring, hints, progress, mistake capture.
- Mock exam flow with preserved Streamlit session timer/answers and automatic expiry handling.
- Summarizer styles, notes, flashcard ratings/download, material chat, and mistake search/status.
- Automated tests for storage, validation, scoring, chunking, and count constraints.

Verification performed:

- `python3 -m py_compile app.py core/*.py` — passed.
- `.venv/bin/pytest -q` — **3 passed**.
- Headless Streamlit launch on port 8501 — health endpoint returned `ok`; initial HTML page returned successfully.
- Gemini requests were not made during tests or smoke checks, so no API quota was consumed.

Known limitations:

- Gemini API access, YouTube transcript retrieval, and public URL availability depend on external access and the user’s API key.
- The current chat retrieval uses bounded source context rather than a full vector database; it does not fabricate citations and explicitly asks the model to stay within supplied content.
- SQLite on Streamlit Community Cloud is not durable across all redeployments.
- Legacy binary `.ppt` parsing is not included; upload `.pptx`.
