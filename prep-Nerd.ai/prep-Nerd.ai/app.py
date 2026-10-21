import csv
import difflib
import hashlib
import html
import io
import json
import random
import re
import time
from datetime import datetime, timedelta, timezone

import streamlit as st

from core.config import (
    ANALYSIS_DEPTHS,
    DB_PATH,
    DIFFICULTIES,
    LOCAL_DEMO,
    MODEL,
    QUESTION_COUNTS,
    SUMMARY_STYLES,
)
from core.db import Database
from core.extraction import content_hash, extract_file, extract_url
from core.ai import AIError, GeminiService
from core.logic import mistake_from_question, score_questions
from core.validation import Flashcard, QuizPayload


st.set_page_config(
    page_title="prep-Nerd.ai | Your study space",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Microsoft Fluent-inspired system: Segoe UI, neutral surfaces, restrained Azure
# blue, visible focus rings, and high-contrast form controls.
st.markdown(
    """
    <style>
    :root {
      --fluent-brand:#0f6cbd; --fluent-brand-hover:#115ea3; --fluent-brand-pressed:#0c3b5e;
      --fluent-ink:#242424; --fluent-muted:#616161; --fluent-subtle:#8a8886;
      --fluent-line:#d1d1d1; --fluent-line-soft:#e5e5e5; --fluent-canvas:#f5f5f5;
      --fluent-card:#ffffff; --fluent-tint:#eff6fc; --fluent-green:#107c10;
      --fluent-warn:#986f0b; --fluent-danger:#c50f1f;
    }
    html, body, [class*="css"], button, input, textarea, select {
      font-family:"Segoe UI", "Segoe UI Variable", system-ui, -apple-system, sans-serif !important;
    }
    .stApp { background:var(--fluent-canvas); color:var(--fluent-ink); }
    [data-testid="stHeader"] { background:rgba(245,245,245,.96); }
    [data-testid="stMainBlockContainer"] { max-width:1360px; padding-top:1.7rem; padding-bottom:4rem; }
    h1,h2,h3,h4 { font-family:"Segoe UI Variable","Segoe UI",sans-serif !important; color:var(--fluent-ink); letter-spacing:-.025em; }
    h1 { font-size:clamp(1.9rem,3vw,2.55rem) !important; line-height:1.15 !important; font-weight:650 !important; }
    h2 { font-size:1.55rem !important; font-weight:650 !important; }
    h3 { font-size:1.16rem !important; font-weight:650 !important; }
    p, label, .stMarkdown { color:var(--fluent-ink); }
    [data-testid="stSidebar"] { background:#faf9f8; border-right:1px solid var(--fluent-line-soft); }
    [data-testid="stSidebar"] > div:first-child { padding:1.15rem .85rem 1.2rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:var(--fluent-muted); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
      border-radius:5px; padding:.37rem .55rem; margin:.05rem 0; color:#424242; font-weight:550;
      transition:background .15s ease,color .15s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#f0efee; }
    [data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + div { color:var(--fluent-brand); font-weight:650; }
    [data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color:var(--fluent-brand); }
    [data-testid="stMetric"] { background:var(--fluent-card); border:1px solid var(--fluent-line-soft); border-radius:8px; padding:1rem 1.1rem; box-shadow:0 1px 2px rgba(0,0,0,.04); }
    [data-testid="stMetricLabel"] p { color:var(--fluent-muted); font-size:.84rem; font-weight:550; }
    [data-testid="stMetricValue"] { color:var(--fluent-ink); font-size:1.8rem; font-weight:650; }
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button {
      min-height:2.45rem; border-radius:5px; border:1px solid var(--fluent-line); background:#fff;
      color:var(--fluent-ink); font-weight:600; transition:background .14s ease,border-color .14s ease,box-shadow .14s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {
      border-color:#8a8886; background:#f8f8f8; color:var(--fluent-ink);
    }
    .stButton > button:focus-visible, .stDownloadButton > button:focus-visible,
    input:focus-visible, textarea:focus-visible, [data-baseweb="select"]:focus-within {
      outline:2px solid var(--fluent-brand) !important; outline-offset:2px !important;
      box-shadow:0 0 0 1px white !important;
    }
    .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
      color:white; background:var(--fluent-brand); border-color:var(--fluent-brand);
    }
    .stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
      color:white; background:var(--fluent-brand-hover); border-color:var(--fluent-brand-hover);
    }
    .stTextInput input, .stTextArea textarea, .stNumberInput input, [data-testid="stChatInput"] textarea {
      color:var(--fluent-ink) !important; caret-color:var(--fluent-brand) !important;
      -webkit-text-fill-color:var(--fluent-ink) !important; background:#fff !important;
      border-radius:5px !important; border:1px solid #8a8886 !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder, [data-testid="stChatInput"] textarea::placeholder {
      color:#616161 !important; -webkit-text-fill-color:#616161 !important; opacity:1 !important;
    }
    [data-baseweb="select"] > div { border-radius:5px; border-color:#8a8886; background:white; }
    [data-baseweb="popover"] [role="option"] { color:var(--fluent-ink); }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:.25rem; border-bottom:1px solid var(--fluent-line-soft); }
    [data-testid="stTabs"] [data-baseweb="tab"] { color:var(--fluent-muted); font-weight:550; padding:.65rem .85rem; }
    [data-testid="stTabs"] [aria-selected="true"] { color:var(--fluent-brand); border-bottom-color:var(--fluent-brand) !important; }
    [data-testid="stFileUploader"] section { border-radius:6px; border-color:#c8c6c4; background:#fff; }
    [data-testid="stExpander"] { border:1px solid var(--fluent-line-soft); border-radius:6px; background:#fff; }
    [data-testid="stChatMessage"] { background:#fff; border:1px solid var(--fluent-line-soft); border-radius:8px; }
    [data-testid="stProgressBar"] > div > div { background:var(--fluent-brand); }
    [data-testid="stCheckbox"] label, [data-testid="stRadio"] label { color:var(--fluent-ink); }
    hr { border-color:var(--fluent-line-soft); }
    .brand-lockup { display:flex; align-items:center; gap:.65rem; margin:0 0 1.35rem .25rem; }
    .brand-mark { display:grid; place-items:center; width:36px; height:36px; border-radius:7px; background:var(--fluent-brand); color:white; font-size:17px; font-weight:700; }
    .brand-name { font-size:1.02rem; font-weight:700; letter-spacing:-.025em; color:var(--fluent-ink); }
    .brand-tag { color:var(--fluent-muted); font-size:.7rem; margin-top:.04rem; }
    .eyebrow { color:var(--fluent-brand); font-size:.76rem; font-weight:650; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.55rem; }
    .hero { position:relative; overflow:hidden; padding:2.15rem 2.25rem; border-radius:9px; background:linear-gradient(112deg,#eff6fc,#f7f7f7 72%); border:1px solid #d9eaf8; margin-bottom:1.35rem; }
    .hero:after { content:""; position:absolute; width:250px; height:250px; right:-65px; top:-130px; border-radius:50%; border:1px solid rgba(15,108,189,.17); box-shadow:0 0 0 26px rgba(15,108,189,.035),0 0 0 54px rgba(15,108,189,.025); }
    .hero h1 { max-width:710px; margin:.2rem 0 .6rem; }
    .hero p { color:#424242; font-size:1rem; max-width:650px; margin:0; line-height:1.6; }
    .section-heading { display:flex; align-items:baseline; justify-content:space-between; gap:.7rem; margin:1.75rem 0 .75rem; }
    .section-heading h3 { margin:0; }
    .section-note { color:var(--fluent-muted); font-size:.84rem; }
    .tool-card { height:100%; min-height:154px; padding:1.05rem 1.1rem; background:#fff; border:1px solid var(--fluent-line-soft); border-radius:7px; box-shadow:0 1px 2px rgba(0,0,0,.035); transition:transform .16s ease,box-shadow .16s ease; }
    .tool-card:hover { transform:translateY(-2px); box-shadow:0 5px 14px rgba(0,0,0,.08); }
    .tool-icon { width:36px; height:36px; border-radius:7px; display:grid; place-items:center; background:var(--fluent-tint); color:var(--fluent-brand); font-size:1rem; font-weight:700; margin-bottom:.8rem; }
    .tool-card h4 { margin:0 0 .3rem; font-size:.98rem; font-weight:650; letter-spacing:-.015em; }
    .tool-card p { color:var(--fluent-muted); font-size:.84rem; line-height:1.48; margin:0; }
    .source-banner { display:flex; gap:.7rem; align-items:flex-start; background:#f1f8f1; border:1px solid #c8e6c9; border-radius:6px; padding:.75rem .9rem; color:#3b633b; font-size:.86rem; margin:.2rem 0 .9rem; }
    .module-intro { color:var(--fluent-muted); margin-top:-.35rem; margin-bottom:1rem; }
    .source-list { background:#fff; border:1px solid var(--fluent-line-soft); border-radius:7px; padding:.25rem 1rem; }
    .source-row { display:flex; justify-content:space-between; gap:1rem; align-items:center; padding:.72rem .1rem; border-bottom:1px solid #f0f0f0; }
    .source-row:last-child { border-bottom:0; }
    .source-title { color:var(--fluent-ink); font-weight:600; }
    .source-meta { color:var(--fluent-muted); font-size:.8rem; white-space:nowrap; }
    .empty-state { text-align:center; border:1px dashed #c8c6c4; border-radius:7px; padding:1.4rem; color:var(--fluent-muted); background:#fff; }
    .flashcard { min-height:245px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; padding:2rem; border:1px solid #d9eaf8; border-radius:10px; background:linear-gradient(135deg,#fff,#eff6fc); box-shadow:0 3px 12px rgba(0,0,0,.045); animation:flip-in .28s ease; }
    .flashcard.is-back { background:linear-gradient(135deg,#fff,#f1f8f1); border-color:#c8e6c9; }
    .flashcard-label { color:var(--fluent-brand); font-size:.76rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.85rem; }
    .flashcard-copy { color:var(--fluent-ink); font-size:1.16rem; line-height:1.55; max-width:740px; }
    @keyframes flip-in { from { opacity:.5; transform:rotateY(-9deg) scale(.985); } to { opacity:1; transform:rotateY(0) scale(1); } }
    .auth-panel { max-width:680px; margin:7vh auto 0; background:#fff; border:1px solid var(--fluent-line-soft); border-radius:10px; padding:2rem; box-shadow:0 8px 24px rgba(0,0,0,.06); }
    @media (max-width:700px) { [data-testid="stMainBlockContainer"] { padding:1rem .85rem 2.5rem; } .hero { padding:1.4rem; } .hero:after { right:-170px; } .section-heading { align-items:flex-start; flex-direction:column; gap:.2rem; } .flashcard { min-height:195px; padding:1.25rem; } }
    @media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms !important; transition-duration:.01ms !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def authenticated_user_id():
    """Return a stable opaque owner key, or show a safe sign-in/setup page."""
    if LOCAL_DEMO:
        return "local"
    user = getattr(st, "user", None)
    if user and bool(getattr(user, "is_logged_in", False)):
        subject = getattr(user, "sub", None) or getattr(user, "email", None)
        if subject:
            return hashlib.sha256(str(subject).encode("utf-8")).hexdigest()
    st.markdown(
        '<div class="auth-panel"><div class="brand-lockup"><div class="brand-mark">P</div><div><div class="brand-name">prep-Nerd.ai</div><div class="brand-tag">A focused workspace for learning</div></div></div>',
        unsafe_allow_html=True,
    )
    st.title("Sign in to your study space")
    st.write("Your sources, chats, flashcards, progress, and mistakes are kept in a separate account workspace.")
    if hasattr(st, "login"):
        if st.button("Continue with Google", type="primary"):
            try:
                st.login()
            except Exception as exc:
                st.error(f"Google sign-in is not configured for this Streamlit app: {exc}")
                st.info("If another Streamlit app already signs in with Google, reuse its client_id and client_secret in this app's private Secrets. Streamlit app secrets are not shared automatically. The existing Google client must also allow this app's /oauth2callback URL; a new client is not required if you can reuse the old one.")
    else:
        st.error("This Streamlit version does not support OIDC sign-in. Install the project requirements and configure Google OAuth.")
    st.caption("This app runs on Streamlit Community Cloud; Manus Website Builder login is separate and is not inherited here. Setup and credential reuse steps are in README.md. For a one-person local preview only, set PREP_NERD_LOCAL_DEMO=true.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


USER_ID = authenticated_user_id()
db = Database(DB_PATH)

for key, default in {
    "answers": {}, "quiz": None, "exam": None, "source": "", "source_id": None,
    "module": "Dashboard", "chat": [], "chat_artifact_id": None, "chat_source_id": None,
    "cards": [], "active_deck_id": None, "flash_index": 0, "flash_revealed": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

MODULES = [
    "Dashboard", "Universal Summarizer", "Flashcards", "Chat with Material",
     "Mock Exam", "Mistake Notebook",
]


def go_to(target):
    st.session_state.module = target


with st.sidebar:
    st.markdown(
        '<div class="brand-lockup"><div class="brand-mark">P</div><div><div class="brand-name">prep-Nerd.ai</div><div class="brand-tag">Your personal study space</div></div></div>',
        unsafe_allow_html=True,
    )
    st.caption("WORKSPACE")
    module = st.radio("Navigate", MODULES, label_visibility="collapsed", key="module")
    st.divider()
    st.caption(f"AI model · {MODEL}")
    depth = st.selectbox("Analysis depth", ANALYSIS_DEPTHS, index=2, key="analysis_depth")
    st.markdown(
        '<div style="margin-top:1rem;padding:.8rem;border-radius:6px;background:#f0efee;color:#616161;font-size:.79rem;line-height:1.5">A focused workspace to turn learning material into understanding.</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    identity = "Local demo" if LOCAL_DEMO else (getattr(st.user, "email", None) or "Signed in")
    st.caption(f"Signed in · {identity}")
    if not LOCAL_DEMO and hasattr(st, "logout") and st.button("Sign out", use_container_width=True):
        st.logout()


def section_title(title, subtitle=None):
    st.title(title)
    if subtitle:
        st.markdown(f'<p class="module-intro">{html.escape(subtitle)}</p>', unsafe_allow_html=True)


def source_box(scope="default"):
    safe_scope = re.sub(r"[^a-zA-Z0-9_-]", "_", scope)
    st.markdown(
        '<div class="section-heading"><h3>Choose your study material</h3><span class="section-note">Add a source once, then use it across your tools</span></div>',
        unsafe_allow_html=True,
    )
    saved_sources = db.sources(user_id=USER_ID)
    if saved_sources:
        with st.expander("Load a source saved to your account", expanded=False):
            saved_source_id = st.selectbox(
                "Saved sources", [item["id"] for item in saved_sources],
                format_func=lambda value: next((item["title"] for item in saved_sources if item["id"] == value), "Saved source"),
                key=f"saved_source_{safe_scope}",
            )
            if st.button("Use selected source", key=f"load_source_{safe_scope}"):
                source = next(item for item in saved_sources if item["id"] == saved_source_id)
                st.session_state.source = source["content"]
                st.session_state.source_id = source["id"]
                st.rerun()
    tab1, tab2, tab3 = st.tabs(["Topic or pasted text", "Upload a file", "Add a public URL"])
    with tab1:
        topic = st.text_input("Topic", key=f"topic_{safe_scope}", placeholder="For example: Cell division, World War II, or SQL joins")
        pasted = st.text_area("Paste notes or reading material", key=f"pasted_{safe_scope}", height=125, placeholder="Paste a passage, your notes, or a lesson transcript…")
    with tab2:
        uploaded = st.file_uploader("Drop a file here or browse", key=f"upload_{safe_scope}", type=["txt", "pdf", "md", "markdown", "pptx", "docx"], help="TXT, PDF, Markdown, PPTX, or DOCX · up to 20 MB")
    with tab3:
        url = st.text_input("Public webpage or YouTube URL", key=f"url_{safe_scope}", placeholder="https://…")

    if st.button("Process and save source", type="primary", key=f"process_source_{safe_scope}"):
        try:
            if uploaded:
                text = extract_file(uploaded)
                title, ref, kind = uploaded.name, uploaded.name, "file"
            elif url.strip():
                text, ref = extract_url(url.strip())
                title, kind = ref, "url"
            elif pasted.strip() or topic.strip():
                text = pasted.strip() or topic.strip()
                title, ref, kind = topic.strip() or "Pasted notes", "", "text"
            else:
                st.warning("Add a topic, paste some text, upload a file, or enter a URL first.")
                return st.session_state.get("source", "")
            if len(text.strip()) < 10:
                st.warning("This source looks a little short. Please add more material and try again.")
                return st.session_state.get("source", "")
            source_id = db.add_source(title, kind, text, ref, user_id=USER_ID)
            st.session_state.source = text
            st.session_state.source_id = source_id
            st.success(f"Saved **{title}** · {len(text):,} characters ready to study")
            return text
        except Exception as exc:
            st.error(str(exc))
    current_source = st.session_state.get("source", "")
    if current_source:
        st.markdown(
            f'<div class="source-banner"><span>✓</span><span><strong>Study material ready.</strong> {len(current_source):,} characters are available to this tool.</span></div>',
            unsafe_allow_html=True,
        )
    return current_source


def ai():
    return GeminiService()


def ai_text(task, content):
    try:
        with st.spinner("Working through your material…"):
            return ai().analyze(task, content, depth)
    except AIError as exc:
        st.error(str(exc))
        return None


def dashboard():
    st.markdown(
        '<div class="hero"><div class="eyebrow">Your learning workspace</div><h1>Make your study time<br>count for more.</h1><p>Bring in your learning material, then turn it into clear explanations, useful practice, and a revision plan that works for you.</p></div>',
        unsafe_allow_html=True,
    )
    sources = db.sources(user_id=USER_ID)
  
    cards_count = len(db.artifacts("flashcards", user_id=USER_ID))
    mistakes_count = sum(item["status"] != "Reviewed" for item in db.mistakes(user_id=USER_ID))
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Sources added", len(sources)), ("Flashcard decks", cards_count), ("To review", mistakes_count)]):
        col.metric(label, value)

    st.markdown('<div class="section-heading"><h3>Your learning toolkit</h3><span class="section-note">Pick up wherever you need help</span></div>', unsafe_allow_html=True)
    tools = [
        ("S", "Universal Summarizer", "Find the key ideas in a format that suits the way you revise.", "Universal Summarizer"),
        ("F", "Flashcards", "Practice active recall, track mastery, and resume a deck.", "Flashcards"),
        ("A", "Chat with Material", "Ask natural questions grounded in relevant source passages.", "Chat with Material"),
        ("E", "Mock Exam", "Test yourself with a timed practice exam.", "Mock Exam"),
        ("↗", "Mistake Notebook", "Revisit missed questions and track what you have reviewed.", "Mistake Notebook"),
    ]
    for start in range(0, len(tools), 3):
        cols = st.columns(3)
        for col, (icon, title, description, target) in zip(cols, tools[start:start + 3]):
            with col:
                st.markdown(
                    f'<div class="tool-card"><div class="tool-icon">{html.escape(icon)}</div><h4>{html.escape(title)}</h4><p>{html.escape(description)}</p></div>',
                    unsafe_allow_html=True,
                )
                st.button("Open tool  →", key=f"open_{target}", on_click=go_to, args=(target,), use_container_width=True)

    st.markdown('<div class="section-heading"><h3>Recently added material</h3><span class="section-note">Private to your account</span></div>', unsafe_allow_html=True)
    if sources:
        rows = []
        for source in sources[:6]:
            title = html.escape(str(source.get("title", "Untitled source")))
            kind = html.escape(str(source.get("kind", "source")).title())
            created = html.escape(str(source.get("created_at", "")))
            rows.append(f'<div class="source-row"><span class="source-title">{title}</span><span class="source-meta">{kind} · {created}</span></div>')
        st.markdown('<div class="source-list">' + "".join(rows) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><strong>No sources yet.</strong><br>Add a topic, notes, file, or URL in any tool to get started.</div>', unsafe_allow_html=True)


def quiz_page(exam=False):
    title = "Mock Exam" if exam else "Quiz Generator"
    intro = "Practice under a timer, then review your results." if exam else "Create a quick practice set from the material you are learning."
    section_title(title, intro)
    content = source_box("mock-exam" if exam else "quiz")
    col1, col2 = st.columns(2)
    with col1:
        count = st.selectbox("Number of questions", QUESTION_COUNTS, index=0, key=f"question_count_{exam}")
    with col2:
        difficulty = st.selectbox("Difficulty", DIFFICULTIES, index=1, key=f"difficulty_{exam}")
    minutes = None
    if exam:
        minutes = st.slider("Time limit", 5, 90, 20, format="%d minutes", key="exam_time_limit")
        st.caption("Your answers are kept as you move through the exam. Correct answers appear after submission.")

    if st.button("Generate questions", type="primary", disabled=not bool(content), key=f"generate_questions_{exam}"):
        prompt = (
            f'Create exactly {count} unique multiple-choice questions at {difficulty} difficulty. '
            f'Return ONLY JSON: {{"questions":[{{"question":str,"options":{{"A":str,"B":str,"C":str,"D":str}},'
            f'"correct_answer":"A|B|C|D","explanation":str,"hint":str,"topic":str,"difficulty":str}}]}}. Source: {content}'
        )
        try:
            parsed = QuizPayload.model_validate(ai().json(prompt)).model_dump()
            if exam:
                st.session_state.exam = {"questions": parsed["questions"], "started": time.time(), "limit": minutes * 60, "submitted": False, "results_saved": False}
                st.session_state.quiz = None
            else:
                st.session_state.quiz = {"questions": parsed["questions"], "submitted": False, "results_saved": False}
                st.session_state.exam = None
            st.session_state.answers = {}
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    state = st.session_state.exam if exam else st.session_state.quiz
    if not state:
        return
    questions = state["questions"]
    submitted = state.get("submitted", False)
    if exam and not submitted:
        remaining = max(0, int(state["limit"] - (time.time() - state["started"])))
        st.progress(len(st.session_state.answers) / max(1, len(questions)))
        st.markdown(f"**Time remaining** · {remaining // 60:02d}:{remaining % 60:02d}")
        if remaining <= 0:
            submitted = True
            state["submitted"] = True
            st.warning("Time expired. Your exam has been submitted.")

    for index, question in enumerate(questions):
        st.markdown(f"#### {index + 1}. {question['question']}")
        choice = st.radio(
            "Choose one answer", list(question["options"]),
            format_func=lambda key, options=question["options"]: f"{key}. {options[key]}",
            key=f'{"exam" if exam else "quiz"}_{index}', index=None,
            disabled=submitted, label_visibility="collapsed",
        )
        if choice:
            st.session_state.answers[index] = choice
        if not exam and question.get("hint") and st.checkbox("Show a hint", key=f"hint_{index}"):
            st.info(question["hint"])
        if submitted and not exam:
            st.markdown(f"**Correct answer: {question['correct_answer']}** · {question['explanation']}")
        st.divider()

    if st.button("Submit exam" if exam else "Check my answers", disabled=submitted, key=f"submit_{exam}"):
        state["submitted"] = True
        st.rerun()
    if submitted:
        result = score_questions(questions, st.session_state.answers)
        st.success(f"Your score: **{result['correct']} / {result['total']}** · {result['percentage']}% · {result['unanswered']} unanswered")
        if not state.get("results_saved"):
            db.save("exam_results" if exam else "quiz_results", title, result, user_id=USER_ID)
            for index, question in enumerate(questions):
                if st.session_state.answers.get(index) != question["correct_answer"]:
                    db.add_mistake(mistake_from_question(question, st.session_state.answers.get(index)), user_id=USER_ID)
            state["results_saved"] = True
        if st.button("Start a new set", key=f"new_set_{exam}"):
            st.session_state.answers = {}
            if exam:
                st.session_state.exam = None
            else:
                st.session_state.quiz = None
            st.rerun()


def text_module(kind, label, task):
    description = "Choose a source and a format; your draft is saved to your account so you can copy or download it." if kind == "summary" else "Turn a source into organized revision notes with the details that matter most."
    section_title(label, description)
    content = source_box(kind)
    saved_drafts = db.artifacts(kind, user_id=USER_ID)
    if saved_drafts:
        with st.expander("Open a saved draft", expanded=False):
            saved_draft_id = st.selectbox(
                "Saved drafts", [item["id"] for item in saved_drafts],
                format_func=lambda value: next((item["title"] for item in saved_drafts if item["id"] == value), "Saved draft"),
                key=f"saved_draft_{kind}",
            )
            if st.button("Load selected draft", key=f"load_draft_{kind}"):
                selected_draft = next(item for item in saved_drafts if item["id"] == saved_draft_id)
                payload = selected_draft.get("payload", {})
                if isinstance(payload, dict) and payload.get("text"):
                    st.session_state[f"output_{kind}"] = payload["text"]
                    st.session_state[f"output_id_{kind}"] = selected_draft["id"]
                    st.session_state[f"edit_output_{kind}"] = payload["text"]
                    st.rerun()
    styles = SUMMARY_STYLES if kind == "summary" else ["Concise revision notes", "Detailed study notes"]
    style = st.selectbox("Output style", styles, key=f"style_{kind}")
    if st.button(f"Generate {label.lower()}", type="primary", disabled=not bool(content), key=f"generate_{kind}"):
        output = ai_text(
            f"{task}. Style: {style}. Use headings, definitions, key concepts, examples, comparisons, formulas where relevant, revision points, and possible exam questions.",
            content,
        )
        if output:
            artifact_id = db.save(kind, label, {"text": output, "style": style, "source_hash": content_hash(content)}, user_id=USER_ID)
            st.session_state[f"output_{kind}"] = output
            st.session_state[f"output_id_{kind}"] = artifact_id
            st.session_state[f"edit_output_{kind}"] = output
            st.rerun()
    output = st.session_state.get(f"output_{kind}")
    if output:
        st.markdown('<div class="section-heading"><h3>Your draft</h3><span class="section-note">Edit and save your changes</span></div>', unsafe_allow_html=True)
        edited = st.text_area("Generated content", output, height=430, key=f"edit_output_{kind}", label_visibility="collapsed")
        c1, c2 = st.columns([1, 3])
        if c1.button("Save changes", key=f"save_output_{kind}"):
            artifact_id = st.session_state.get(f"output_id_{kind}")
            payload = {"text": edited, "style": style, "source_hash": content_hash(content) if content else ""}
            if artifact_id and db.update_artifact(artifact_id, payload, user_id=USER_ID):
                st.session_state[f"output_{kind}"] = edited
                st.success("Draft saved to your account.")
            else:
                st.error("This draft could not be updated. Generate it again and retry.")
        c2.download_button("Download as text", edited, file_name=f"{kind}.txt", mime="text/plain", key=f"download_{kind}")


def _normalise_deck_payload(payload):
    if isinstance(payload, list):
        cards = payload
        index = 0
    elif isinstance(payload, dict):
        cards = payload.get("cards", [])
        index = int(payload.get("review_index", payload.get("index", 0)) or 0)
    else:
        cards, index = [], 0
    for card in cards:
        legacy = card.get("rating", "Again")
        card["rating"] = {"Needs Review": "Again", "Difficult": "Hard"}.get(legacy, legacy)
        card.setdefault("review_count", 0)
        card.setdefault("mastery", 0)
        card.setdefault("interval_days", 0)
    return {"cards": cards, "review_index": index}


def _save_deck(artifact_id, payload, title=None):
    return db.update_artifact(artifact_id, payload, title=title, user_id=USER_ID)


def flashcards():
    section_title("Flashcards", "Build active-recall decks, rate each review, and resume your progress later.")
    content = source_box("flashcards")
    name_col, count_col = st.columns([2, 1])
    with name_col:
        deck_name = st.text_input("Deck name", value="", key="new_deck_name", placeholder="e.g. Cell biology · Unit 3")
    with count_col:
        number = st.number_input("Number of cards", min_value=3, max_value=50, value=10, step=1, key="new_card_count")
    if st.button("Generate a deck", type="primary", disabled=not bool(content), key="generate_flashcards"):
        try:
            raw = ai().json(
                f'Create {number} concise, non-duplicative study flashcards. Return JSON '
                f'{{"cards":[{{"front":str,"back":str}}]}}. Ground every card in this source: {content}'
            )
            cards = [Flashcard.model_validate(card).model_dump() for card in raw["cards"]]
            cards = cards[:int(number)]
            for card in cards:
                card.update({"rating": "Again", "review_count": 0, "mastery": 0, "interval_days": 0, "last_reviewed": None})
            title = deck_name.strip() or "Generated flashcards"
            artifact_id = db.save("flashcards", title, {"cards": cards, "review_index": 0, "source_id": st.session_state.get("source_id")}, user_id=USER_ID)
            st.session_state.active_deck_id = artifact_id
            st.session_state.flash_index = 0
            st.session_state.flash_revealed = False
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    decks = db.artifacts("flashcards", user_id=USER_ID)
    if not decks:
        st.markdown('<div class="empty-state"><strong>No decks yet.</strong><br>Add study material above, name a deck, and generate cards to start.</div>', unsafe_allow_html=True)
        return
    ids = [item["id"] for item in decks]
    active_id = st.session_state.get("active_deck_id")
    active_index = ids.index(active_id) if active_id in ids else 0
    selected_id = st.selectbox("Your saved decks", ids, index=active_index, format_func=lambda value: next((item["title"] for item in decks if item["id"] == value), "Saved deck"), key="deck_picker")
    selected_deck = next(item for item in decks if item["id"] == selected_id)
    if selected_id != st.session_state.get("active_deck_id"):
        st.session_state.active_deck_id = selected_id
        saved_deck = _normalise_deck_payload(selected_deck.get("payload"))
        st.session_state.flash_index = saved_deck.get("review_index", 0)
        st.session_state.flash_revealed = False
    deck = _normalise_deck_payload(selected_deck.get("payload"))
    cards = deck["cards"]
    if not cards:
        st.warning("This deck has no cards.")
        return
    st.markdown(f"**{len(cards)} cards** · saved progress resumes automatically")
    mode = st.selectbox("Review mode", ["Flip cards", "Write an answer", "Rapid review", "Difficult only"], key="flash_mode")
    controls = st.columns(3)
    if controls[0].button("Shuffle", key="shuffle_deck"):
        random.shuffle(cards)
        deck["review_index"] = 0
        _save_deck(selected_id, deck)
        st.session_state.flash_index = 0
        st.session_state.flash_revealed = False
        st.rerun()
    if controls[1].button("Reset session", key="reset_deck_session"):
        deck["review_index"] = 0
        _save_deck(selected_id, deck)
        st.session_state.flash_index = 0
        st.session_state.flash_revealed = False
        st.rerun()
    total_reviews = sum(int(card.get("review_count", 0)) for card in cards)
    controls[2].metric("Reviews logged", total_reviews)

    review_cards = [(original_index, card) for original_index, card in enumerate(cards)]
    if mode == "Difficult only":
        review_cards = [(index, card) for index, card in review_cards if card.get("rating") in {"Again", "Hard"}]
    if not review_cards:
        st.success("No difficult cards in this deck. Nice work.")
        return
    index = min(int(st.session_state.get("flash_index", deck.get("review_index", 0))), len(review_cards) - 1)
    original_index, card = review_cards[index]
    st.progress((index + 1) / len(review_cards), text=f"Card {index + 1} of {len(review_cards)}" if mode == "Difficult only" else f"Card {index + 1} of {len(review_cards)}")
    st.caption(f"Current rating · {card.get('rating', 'Again')} · Mastery {int(card.get('mastery', 0))}%")

    revealed = bool(st.session_state.get("flash_revealed", False)) or mode == "Rapid review"
    card_class = "is-back" if revealed else "is-front"
    card_text = card.get("back", "") if revealed else card.get("front", "")
    card_label = "Answer" if revealed else "Prompt"
    st.markdown(
        f'<div class="flashcard {card_class}"><div class="flashcard-label">{card_label}</div><div class="flashcard-copy">{html.escape(str(card_text))}</div></div>',
        unsafe_allow_html=True,
    )
    if mode == "Write an answer":
        answer = st.text_area("Write your answer before revealing", key=f"write_answer_{selected_id}_{original_index}", height=90, placeholder="Recall the answer in your own words…")
        if st.button("Compare with answer", key=f"compare_{selected_id}_{original_index}"):
            similarity = difflib.SequenceMatcher(None, answer.strip().lower(), str(card.get("back", "")).strip().lower()).ratio() if answer.strip() else 0
            st.session_state[f"answer_similarity_{selected_id}_{original_index}"] = similarity
            st.session_state.flash_revealed = True
            st.rerun()
    elif mode != "Rapid review" and not revealed:
        if st.button("Flip card · reveal answer", type="primary", key=f"flip_{selected_id}_{original_index}"):
            st.session_state.flash_revealed = True
            st.rerun()
    elif mode == "Rapid review" and not revealed:
        st.session_state.flash_revealed = True
        st.rerun()

    if revealed and mode == "Write an answer":
        similarity = st.session_state.get(f"answer_similarity_{selected_id}_{original_index}")
        if similarity is not None:
            st.info(f"Rough text similarity: {similarity:.0%}. This is string overlap, not semantic grading; compare your response with the reference and self-rate.")
        st.markdown("**Reference answer**")
        st.write(card.get("back", ""))
    if revealed:
        st.markdown("**How well did you recall it?**")
        rating_cols = st.columns(4)
        for col, rating in zip(rating_cols, ["Again", "Hard", "Good", "Easy"]):
            if col.button(rating, key=f"rate_{selected_id}_{original_index}_{rating}", use_container_width=True):
                old_interval = float(card.get("interval_days", 0) or 0)
                if rating == "Again":
                    next_interval = 0
                    card["mastery"] = max(0, int(card.get("mastery", 0)) - 10)
                elif rating == "Hard":
                    next_interval = max(1, round(old_interval * 1.2))
                    card["mastery"] = min(100, int(card.get("mastery", 0)) + 8)
                elif rating == "Good":
                    next_interval = max(1, round(old_interval * 2))
                    card["mastery"] = min(100, int(card.get("mastery", 0)) + 16)
                else:
                    next_interval = max(4, round(old_interval * 2.5))
                    card["mastery"] = min(100, int(card.get("mastery", 0)) + 22)
                card["rating"] = rating
                card["review_count"] = int(card.get("review_count", 0)) + 1
                card["interval_days"] = next_interval
                card["last_reviewed"] = datetime.now(timezone.utc).isoformat()
                card["due_at"] = (datetime.now(timezone.utc) + timedelta(days=next_interval)).isoformat() if next_interval else datetime.now(timezone.utc).isoformat()
                if mode == "Difficult only" and rating in {"Good", "Easy"}:
                    next_index = index
                else:
                    next_index = index + 1 if index + 1 < len(review_cards) else 0
                deck["review_index"] = next_index
                _save_deck(selected_id, deck)
                st.session_state.flash_index = deck["review_index"]
                st.session_state.flash_revealed = False
                st.rerun()

    st.markdown("<div class='section-heading'><h3>Deck mastery</h3><span class='section-note'>Ratings and session position are saved in your account</span></div>", unsafe_allow_html=True)
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["front", "back", "rating", "mastery", "review_count", "due_at"])
    for item in cards:
        writer.writerow([item.get("front", ""), item.get("back", ""), item.get("rating", "Again"), item.get("mastery", 0), item.get("review_count", 0), item.get("due_at", "")])
    st.download_button("Download deck as CSV", csv_buffer.getvalue(), file_name=f"{selected_deck['title']}.csv", mime="text/csv", key=f"download_deck_{selected_id}")


def mistakes():
    section_title("Mistake Notebook", "A practical, searchable list of questions worth another look.")
    items = db.mistakes(user_id=USER_ID)
    search = st.text_input("Search by question or topic", placeholder="Try a keyword…", key="mistake_search")
    if not items:
        st.markdown('<div class="empty-state"><strong>Your notebook is clear.</strong><br>Missed answers from completed quizzes and exams will appear here.</div>', unsafe_allow_html=True)
        return
    shown = 0
    for item in items:
        payload = item["payload"]
        haystack = f"{payload.get('question', '')} {payload.get('topic', '')}".lower()
        if search and search.lower() not in haystack:
            continue
        shown += 1
        with st.expander(f"{payload.get('topic', 'Review')} · {item.get('status', 'To review')} · {payload.get('question', '')}"):
            st.markdown(f"**Your answer:** {payload.get('selected_answer') or 'Unanswered'}  ·  **Correct:** {payload.get('correct_answer', '—')}")
            st.caption(payload.get("explanation", ""))
            if item.get("status") != "Reviewed" and st.button("Mark as reviewed", key=f"mark_{item['id']}"):
                db.update_mistake(item["id"], "Reviewed", user_id=USER_ID)
                st.rerun()
    if not shown:
        st.info("No mistakes match that search.")


def chat():
    section_title("Chat with Material", "Ask naturally. Answers use relevant passages from your notes and keep extra context clearly labeled.")
    content = source_box("chat")
    if not content:
        st.info("Add study material above to start a grounded conversation.")
        return
    source_id = st.session_state.get("source_id")
    if source_id != st.session_state.get("chat_source_id"):
        stored = next((item for item in db.artifacts("chat", user_id=USER_ID) if item.get("title") == f"chat:{source_id}"), None)
        payload = stored.get("payload", {}) if stored else {}
        st.session_state.chat = payload.get("messages", []) if isinstance(payload, dict) else []
        st.session_state.chat_artifact_id = stored.get("id") if stored else None
        st.session_state.chat_source_id = source_id
    question = st.chat_input("Ask about a concept, synonym, example, or follow-up…")
    if question:
        history = list(st.session_state.get("chat", []))
        history.append({"role": "user", "content": question})
        ai_history = [(item.get("role", "user"), item.get("content", "")) for item in st.session_state.chat]
        try:
            with st.spinner("Finding relevant passages and composing an answer…"):
                answer = ai().answer_question(question, content, history=ai_history)
            history.append({"role": "assistant", "content": answer})
            st.session_state.chat = history
            payload = {"source_id": source_id, "messages": history}
            artifact_id = st.session_state.get("chat_artifact_id")
            if artifact_id and db.update_artifact(artifact_id, payload, user_id=USER_ID):
                pass
            else:
                st.session_state.chat_artifact_id = db.save("chat", f"chat:{source_id}", payload, user_id=USER_ID)
        except AIError as exc:
            st.error(str(exc))
    for message in st.session_state.get("chat", []):
        with st.chat_message(message.get("role", "assistant")):
            st.write(message.get("content", ""))
    if st.session_state.get("chat") and st.button("Clear conversation", key="clear_chat"):
        st.session_state.chat = []
        artifact_id = st.session_state.get("chat_artifact_id")
        if artifact_id:
            db.update_artifact(artifact_id, {"source_id": source_id, "messages": []}, user_id=USER_ID)
        st.rerun()


if module == "Dashboard":
    dashboard()
elif module == "Mock Exam":
    quiz_page(exam=True)
elif module == "Universal Summarizer":
    text_module("summary", "Universal Summarizer", "Summarize the source")
elif module == "Flashcards":
    flashcards()
elif module == "Mistake Notebook":
    mistakes()
elif module == "Chat with Material":
    chat()
