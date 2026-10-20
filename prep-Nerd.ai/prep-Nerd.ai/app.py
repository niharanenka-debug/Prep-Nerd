import html
import json
import time

import streamlit as st

from core.config import *
from core.db import Database
from core.extraction import extract_file, extract_url, content_hash
from core.ai import GeminiService, AIError
from core.logic import normalize_count, score_questions, mistake_from_question
from core.validation import QuizPayload, Flashcard


st.set_page_config(
    page_title="prep-Nerd.ai | Your study space",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A quiet, paper-like visual system with clear hierarchy and restrained accents.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --ink: #182b3a;
        --muted: #71808d;
        --line: #e8edf0;
        --paper: #ffffff;
        --canvas: #f6f8f7;
        --green: #217a63;
        --green-dark: #145c4a;
        --green-soft: #e8f4ef;
        --blue-soft: #edf4fa;
        --amber-soft: #fbf3e7;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: var(--canvas); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(246,248,247,.92); }
    [data-testid="stMainBlockContainer"] { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 4rem; }
    h1, h2, h3, h4 { font-family: 'Manrope', sans-serif; color: var(--ink); letter-spacing: -.035em; }
    h1 { font-size: clamp(2rem, 3.2vw, 2.85rem) !important; line-height: 1.12 !important; font-weight: 800 !important; }
    h2 { font-weight: 750 !important; }
    p, label, .stMarkdown { color: var(--ink); }
    [data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding: 1.5rem 1rem 1.25rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border-radius: 10px; padding: .45rem .55rem; margin: .1rem 0;
        color: #536371; font-weight: 600;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: #f3f7f5; }
    [data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + div { color: var(--green-dark); }
    [data-testid="stSidebar"] [data-testid="stRadio"] input { accent-color: var(--green); }
    [data-testid="stMetric"] {
        background: var(--paper); border: 1px solid var(--line); border-radius: 16px;
        padding: 1rem 1.15rem; box-shadow: 0 5px 20px rgba(24,43,58,.025);
    }
    [data-testid="stMetricLabel"] p { color: var(--muted); font-size: .84rem; font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: 'Manrope', sans-serif; font-weight: 800; }
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px; border: 1px solid #dce6e1; font-weight: 700;
        color: var(--green-dark); background: #fff; transition: .18s ease;
        min-height: 2.55rem;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #8db9a9; color: var(--green-dark); background: #f4faf7;
    }
    .stButton > button[kind="primary"] {
        color: white; background: var(--green); border-color: var(--green);
    }
    .stButton > button[kind="primary"]:hover { background: var(--green-dark); border-color: var(--green-dark); color: white; }
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        border-radius: 10px; border-color: #dfe6e9; background: #fff;
    }
    [data-baseweb="select"] > div { border-radius: 10px; border-color: #dfe6e9; }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .4rem; border-bottom: 1px solid var(--line); }
    [data-testid="stTabs"] [data-baseweb="tab"] { color: var(--muted); font-weight: 650; padding: .7rem .95rem; }
    [data-testid="stTabs"] [aria-selected="true"] { color: var(--green-dark); border-bottom-color: var(--green) !important; }
    [data-testid="stFileUploader"] section { border-radius: 14px; border-color: #dce6e1; background: #fbfdfc; }
    [data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 12px; background: #fff; }
    [data-testid="stChatMessage"] { background: #fff; border: 1px solid var(--line); border-radius: 14px; }
    [data-testid="stProgressBar"] > div > div { background: var(--green); }
    hr { border-color: var(--line); }
    .brand-lockup { display:flex; align-items:center; gap:.7rem; margin:0 0 1.7rem .25rem; }
    .brand-mark { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; background:var(--green-soft); color:var(--green-dark); font-size:19px; }
    .brand-name { font-family:'Manrope',sans-serif; font-size:1.08rem; font-weight:800; letter-spacing:-.04em; color:var(--ink); }
    .brand-tag { color:var(--muted); font-size:.72rem; margin-top:.05rem; }
    .eyebrow { color:var(--green); font-size:.76rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.55rem; }
    .hero {
        position:relative; overflow:hidden; padding:2.3rem 2.4rem; border-radius:22px;
        background:linear-gradient(112deg,#eaf5ef 0%,#f0f6f5 54%,#eef4f8 100%);
        border:1px solid #e1eee7; margin-bottom:1.5rem;
    }
    .hero:after { content:''; position:absolute; width:270px; height:270px; right:-65px; top:-125px; border-radius:50%; border:1px solid rgba(33,122,99,.13); box-shadow:0 0 0 28px rgba(33,122,99,.035),0 0 0 58px rgba(33,122,99,.025); }
    .hero h1 { max-width:710px; margin:.2rem 0 .65rem; }
    .hero p { color:#566c70; font-size:1.02rem; max-width:620px; margin:0; line-height:1.65; }
    .section-heading { display:flex; align-items:baseline; justify-content:space-between; margin:2rem 0 .8rem; }
    .section-heading h3 { font-size:1.18rem; margin:0; font-weight:750; }
    .section-note { color:var(--muted); font-size:.88rem; }
    .tool-card {
        height:100%; min-height:172px; padding:1.2rem 1.25rem; background:#fff;
        border:1px solid var(--line); border-radius:16px; box-shadow:0 6px 22px rgba(24,43,58,.025);
        transition:transform .18s ease, box-shadow .18s ease;
    }
    .tool-card:hover { transform:translateY(-2px); box-shadow:0 12px 28px rgba(24,43,58,.07); }
    .tool-icon { width:40px; height:40px; border-radius:12px; display:grid; place-items:center; background:var(--green-soft); color:var(--green-dark); font-size:1.1rem; font-weight:800; margin-bottom:.95rem; }
    .tool-card h4 { margin:0 0 .35rem; font-size:1rem; font-weight:750; letter-spacing:-.02em; }
    .tool-card p { color:var(--muted); font-size:.87rem; line-height:1.55; margin:0; }
    .source-banner { display:flex; gap:.8rem; align-items:flex-start; background:#f3f8f5; border:1px solid #e2eee7; border-radius:12px; padding:.85rem 1rem; color:#4f6960; font-size:.88rem; margin:.25rem 0 1rem; }
    .module-intro { color:var(--muted); margin-top:-.4rem; margin-bottom:1.15rem; }
    .source-list { background:#fff; border:1px solid var(--line); border-radius:14px; padding:.25rem 1rem; }
    .source-row { display:flex; justify-content:space-between; gap:1rem; align-items:center; padding:.75rem .1rem; border-bottom:1px solid #f0f2f3; }
    .source-row:last-child { border-bottom:0; }
    .source-title { color:var(--ink); font-weight:700; }
    .source-meta { color:var(--muted); font-size:.82rem; white-space:nowrap; }
    .empty-state { text-align:center; border:1px dashed #d9e4df; border-radius:16px; padding:1.5rem; color:var(--muted); background:#fbfdfc; }
    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] { padding:1.2rem 1rem 3rem; }
        .hero { padding:1.55rem; }
        .hero:after { right:-160px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


db = Database(DB_PATH)

# Stable session state across Streamlit reruns.
for key, default in {
    "answers": {},
    "quiz": None,
    "exam": None,
    "source": "",
    "source_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

MODULES = [
    "Dashboard",
    "Universal Summarizer",
    "Flashcards",
    "Chat with Material",
    "Notes Generator",
    "Mock Exam",
    "Mistake Notebook",
]


def go_to(target):
    st.session_state.module = target


with st.sidebar:
    st.markdown(
        '<div class="brand-lockup"><div class="brand-mark">✦</div><div><div class="brand-name">prep-Nerd.ai</div><div class="brand-tag">Your personal study space</div></div></div>',
        unsafe_allow_html=True,
    )
    st.caption("LEARN")
    module = st.radio("Navigate", MODULES, label_visibility="collapsed", key="module")
    st.divider()
    st.caption(f"AI model · {MODEL}")
    depth = st.selectbox("Analysis depth", ANALYSIS_DEPTHS, index=2)
    st.markdown(
        '<div style="margin-top:1.1rem;padding:.8rem .85rem;border-radius:12px;background:#f5f8f6;color:#71808d;font-size:.8rem;line-height:1.5">A focused workspace to turn learning material into understanding.</div>',
        unsafe_allow_html=True,
    )


def section_title(title, subtitle=None):
    st.title(title)
    if subtitle:
        st.markdown(f'<p class="module-intro">{html.escape(subtitle)}</p>', unsafe_allow_html=True)


def source_box():
    st.markdown('<div class="section-heading"><h3>Choose your study material</h3><span class="section-note">Add a source once, then use it across your tools</span></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Topic or pasted text", "Upload a file", "Add a public URL"])
    with tab1:
        topic = st.text_input("Topic", placeholder="For example: Cell division, World War II, or SQL joins")
        pasted = st.text_area("Paste notes or reading material", height=125, placeholder="Paste a passage, your notes, or a lesson transcript…")
    with tab2:
        uploaded = st.file_uploader("Drop a file here or browse", type=["txt", "pdf", "md", "markdown", "pptx", "docx"], help="TXT, PDF, Markdown, PPTX, or DOCX · up to 20 MB")
    with tab3:
        url = st.text_input("Public webpage or YouTube URL", placeholder="https://…")

    if st.button("Process and save source", type="primary", key="process_source"):
        try:
            if uploaded:
                text = extract_file(uploaded)
                title = uploaded.name
                ref = uploaded.name
                kind = "file"
            elif url.strip():
                text, ref = extract_url(url.strip())
                title = ref
                kind = "url"
            elif pasted.strip() or topic.strip():
                text = pasted.strip() or topic.strip()
                title = topic.strip() or "Pasted notes"
                ref = ""
                kind = "text"
            else:
                st.warning("Add a topic, paste some text, upload a file, or enter a URL first.")
                return st.session_state.get("source", "")

            if len(text.strip()) < 10:
                st.warning("This source looks a little short. Please add more material and try again.")
                return st.session_state.get("source", "")

            sid = db.add_source(title, kind, text, ref)
            st.session_state.source = text
            st.session_state.source_id = sid
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
        '<div class="hero"><div class="eyebrow">A better way to study</div><h1>Make your study time<br>count for more.</h1><p>Bring in your learning material, then turn it into clear explanations, useful practice, and a revision plan that works for you.</p></div>',
        unsafe_allow_html=True,
    )
    sources = db.sources()
    notes_count = len(db.artifacts("notes"))
    cards_count = len(db.artifacts("flashcards"))
    mistakes_count = sum(item["status"] != "Reviewed" for item in db.mistakes())
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Sources added", len(sources)), ("Notes created", notes_count), ("Flashcard sets", cards_count), ("To review", mistakes_count)]):
        col.metric(label, value)

    st.markdown('<div class="section-heading"><h3>Your learning toolkit</h3><span class="section-note">Pick up wherever you need help</span></div>', unsafe_allow_html=True)
    tools = [
        ("S", "Universal Summarizer", "Find the key ideas in a format that suits the way you revise.", "Universal Summarizer"),
        ("F", "Flashcards", "Create quick recall prompts and rate what you know.", "Flashcards"),
        ("A", "Chat with Material", "Ask questions and get answers grounded in your source.", "Chat with Material"),
        ("N", "Notes Generator", "Shape dense reading into structured, editable revision notes.", "Notes Generator"),
        ("E", "Mock Exam", "Test yourself with a timed practice exam.", "Mock Exam"),
        ("↗", "Mistake Notebook", "Revisit missed questions and keep track of what you have reviewed.", "Mistake Notebook"),
    ]
    for start in range(0, len(tools), 4):
        chunk = tools[start:start + 4]
        cols = st.columns(4)
        for col, (icon, title, description, target) in zip(cols, chunk):
            with col:
                st.markdown(
                    f'<div class="tool-card"><div class="tool-icon">{html.escape(icon)}</div><h4>{html.escape(title)}</h4><p>{html.escape(description)}</p></div>',
                    unsafe_allow_html=True,
                )
                st.button("Open tool →", key=f"open_{target}", on_click=go_to, args=(target,), use_container_width=True)

    st.markdown('<div class="section-heading"><h3>Recently added material</h3><span class="section-note">Your saved study sources</span></div>', unsafe_allow_html=True)
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
    content = source_box()
    col1, col2 = st.columns(2)
    with col1:
        count = st.selectbox("Number of questions", QUESTION_COUNTS, index=0)
    with col2:
        diff = st.selectbox("Difficulty", DIFFICULTIES, index=1)
    minutes = None
    if exam:
        minutes = st.slider("Time limit", 5, 90, 20, format="%d minutes")
        st.caption("Your answers are kept as you move through the exam. Correct answers appear after submission.")

    if st.button("Generate questions", type="primary", disabled=not bool(content)):
        prompt = f'Create exactly {count} unique multiple-choice questions at {diff} difficulty. Return ONLY JSON: {{"questions":[{{"question":str,"options":{{"A":str,"B":str,"C":str,"D":str}},"correct_answer":"A|B|C|D","explanation":str,"hint":str,"topic":str,"difficulty":str}}]}}. Source: {content}'
        try:
            raw = ai().json(prompt)
            parsed = QuizPayload.model_validate(raw).model_dump()
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
            "Choose one answer",
            list(question["options"]),
            format_func=lambda key, options=question["options"]: f"{key}. {options[key]}",
            key=f'{"exam" if exam else "quiz"}_{index}',
            index=None,
            disabled=submitted,
            label_visibility="collapsed",
        )
        if choice:
            st.session_state.answers[index] = choice
        if not exam and question.get("hint") and st.checkbox("Show a hint", key=f"hint_{index}"):
            st.info(question["hint"])
        if submitted and not exam:
            st.markdown(f"**Correct answer: {question['correct_answer']}** · {question['explanation']}")
        st.divider()

    if st.button("Submit exam" if exam else "Check my answers", disabled=submitted):
        state["submitted"] = True
        st.rerun()

    if submitted:
        result = score_questions(questions, st.session_state.answers)
        st.success(f"Your score: **{result['correct']} / {result['total']}** · {result['percentage']}% · {result['unanswered']} unanswered")
        if not state.get("results_saved"):
            db.save("exam_results" if exam else "quiz_results", title, result)
            for index, question in enumerate(questions):
                if st.session_state.answers.get(index) != question["correct_answer"]:
                    db.add_mistake(mistake_from_question(question, st.session_state.answers.get(index)))
            state["results_saved"] = True
        if st.button("Start a new set"):
            st.session_state.answers = {}
            if exam:
                st.session_state.exam = None
            else:
                st.session_state.quiz = None
            st.rerun()


def text_module(kind, label, task):
    description = "Choose a source and a format; your draft will be saved in your session so you can copy or download it." if kind == "summary" else "Turn a source into organized revision notes with the details that matter most."
    section_title(label, description)
    content = source_box()
    styles = SUMMARY_STYLES if kind == "summary" else ["Concise revision notes", "Detailed study notes"]
    style = st.selectbox("Output style", styles)
    if st.button(f"Generate {label.lower()}", type="primary", disabled=not bool(content)):
        output = ai_text(
            f"{task}. Style: {style}. Use headings, definitions, key concepts, examples, comparisons, formulas where relevant, revision points, and possible exam questions.",
            content,
        )
        if output:
            st.session_state[f"output_{kind}"] = output
            db.save(kind, label, {"text": output, "style": style, "source_hash": content_hash(content)})
    output = st.session_state.get(f"output_{kind}")
    if output:
        st.markdown('<div class="section-heading"><h3>Your draft</h3><span class="section-note">Edit freely before you save it elsewhere</span></div>', unsafe_allow_html=True)
        st.text_area("Generated content", output, height=430, key=f"edit_output_{kind}", label_visibility="collapsed")
        st.download_button("Download as text", output, file_name=f"{kind}.txt", mime="text/plain")


def flashcards():
    section_title("Flashcards", "Build active-recall cards from a source, then rate each one as you review.")
    content = source_box()
    number = st.number_input("Number of cards", min_value=3, max_value=50, value=10, step=1)
    if st.button("Generate flashcards", type="primary", disabled=not bool(content)):
        try:
            raw = ai().json(f'Create {number} concise study flashcards. Return JSON {{"cards":[{{"front":str,"back":str,"rating":"Needs Review"}}]}}. Source: {content}')
            cards = [Flashcard.model_validate(card).model_dump() for card in raw["cards"]]
            db.save("flashcards", "Generated flashcards", cards)
            st.session_state.cards = cards
        except Exception as exc:
            st.error(str(exc))

    cards = st.session_state.get("cards", [])
    if cards:
        st.markdown('<div class="section-heading"><h3>Review your cards</h3><span class="section-note">Open a card to reveal its answer</span></div>', unsafe_allow_html=True)
        ratings = ["Easy", "Needs Review", "Difficult"]
        for index, card in enumerate(cards):
            current_rating = card.get("rating", "Needs Review")
            if current_rating not in ratings:
                current_rating = "Needs Review"
            with st.expander(f"{index + 1:02d}  ·  {card['front']}"):
                st.markdown(card["back"])
                card["rating"] = st.selectbox("How well did you know it?", ratings, index=ratings.index(current_rating), key=f"rating_{index}")
        csv_content = "front,back,rating\n" + "\n".join(
            f'"{card["front"].replace(chr(34), chr(34) * 2)}","{card["back"].replace(chr(34), chr(34) * 2)}",{card["rating"]}'
            for card in cards
        )
        st.download_button("Download cards as CSV", csv_content, file_name="flashcards.csv", mime="text/csv")


def mistakes():
    section_title("Mistake Notebook", "A small, practical list of questions worth another look.")
    items = db.mistakes()
    search = st.text_input("Search by question or topic", placeholder="Try a keyword…")
    if not items:
        st.markdown('<div class="empty-state"><strong>Your notebook is clear.</strong><br>Missed answers from completed quizzes and exams will appear here.</div>', unsafe_allow_html=True)
        return
    for item in items:
        payload = item["payload"]
        haystack = f"{payload.get('question', '')} {payload.get('topic', '')}".lower()
        if search and search.lower() not in haystack:
            continue
        with st.expander(f"{payload.get('topic', 'Review')} · {payload.get('status', 'To review')} · {payload.get('question', '')}"):
            st.markdown(f"**Your answer:** {payload.get('selected_answer') or 'Unanswered'}  ·  **Correct:** {payload.get('correct_answer', '—')}")
            st.caption(payload.get("explanation", ""))
            if payload.get("status") != "Reviewed" and st.button("Mark as reviewed", key=f"mark_{item['id']}"):
                db.update_mistake(item["id"], "Reviewed")
                st.rerun()


def chat():
    section_title("Chat with Material", "Ask a question and get an answer based only on the source you provide.")
    content = source_box()
    if not content:
        st.info("Add study material above to start a grounded conversation.")
    question = st.chat_input("Ask something about your material…", disabled=not bool(content))
    if question and content:
        st.session_state.setdefault("chat", []).append(("user", question))
        answer = ai_text(
            f"Answer only from the provided study material. If unsupported, say you cannot find it. Include a short source passage quote or section reference when available. Question: {question}",
            content,
        )
        if answer:
            st.session_state.chat.append(("assistant", answer))
    for role, message in st.session_state.get("chat", []):
        with st.chat_message(role):
            st.write(message)
    if st.session_state.get("chat") and st.button("Clear conversation"):
        st.session_state.chat = []
        st.rerun()


if module == "Dashboard":
    dashboard()
elif module == "Mock Exam":
    quiz_page(exam=True)
elif module == "Universal Summarizer":
    text_module("summary", "Universal Summarizer", "Summarize the source")
elif module == "Notes Generator":
    text_module("notes", "Notes Generator", "Create revision notes")
elif module == "Flashcards":
    flashcards()
elif module == "Mistake Notebook":
    mistakes()
elif module == "Chat with Material":
    chat()
