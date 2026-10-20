# prep-Nerd.ai

**Read smarter. Understand deeper. Revise faster. Prepare better.**

A Streamlit study workspace integrating seven modules: quiz generation, summarization, flashcards, grounded chat, notes, mock exams, and a mistake notebook.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For AI features, configure a key in one of the formats the app reads:

- Copy `.env.example` to `.env` and set `GEMINI_API_KEY`.
- Or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `GEMINI_API_KEY`.

Example files are templates and are not loaded automatically. Restart Streamlit after creating or changing the configuration.

The app is usable without a key for navigation and persistence, but AI generation reports a clear configuration error rather than fabricating output. The app uses the official `google-genai` SDK (`genai.Client(...).models.generate_content`) and keeps the model configurable with `GEMINI_MODEL`; the default is `gemini-3.8-flash` based on current official documentation.

SQLite is modular and local. Streamlit Community Cloud ephemeral storage should not be treated as permanent production storage. For durable multi-user deployment, replace `core.db.Database` with a managed database adapter.

## Supported source inputs

TXT, PDF, Markdown, PPTX, DOCX, pasted text, topics, and public HTTP/HTTPS pages. Legacy `.ppt` asks for `.pptx`. URL fetching blocks private/internal IP destinations, limits redirects and response size, and never executes retrieved content.

## Tests

```bash
pytest -q
```

Tests cover persistence, extraction chunking, Pydantic validation, question count enforcement, and deterministic scoring. Gemini calls are not made by tests.
