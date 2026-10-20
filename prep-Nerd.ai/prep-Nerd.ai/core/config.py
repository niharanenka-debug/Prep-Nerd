import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
ROOT=Path(__file__).resolve().parents[1]
DB_PATH=Path(os.getenv("DATABASE_PATH", ROOT/"prep_nerd.db"))
MODEL=os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
QUESTION_COUNTS=(5,10,15,20,25)
DIFFICULTIES=("Easy","Medium","Hard")
ANALYSIS_DEPTHS=("Automatic","Quick","Standard","Deep","Exhaustive")
SUMMARY_STYLES=("Executive Summary","Key Takeaways","Detailed Analysis","Short Abstract","Action Items")
SUMMARY_LENGTHS=("Very Short","Medium","Comprehensive")
MAX_QUESTIONS=25

def api_key():
    key=os.getenv("GEMINI_API_KEY")
    if key: return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception: return None
