from datetime import datetime, timezone
from .config import MAX_QUESTIONS,QUESTION_COUNTS
def normalize_count(n:int)->int:
    n=int(n)
    if n not in QUESTION_COUNTS: raise ValueError("Question count must be 5, 10, 15, 20, or 25")
    return min(n,MAX_QUESTIONS)
def score_questions(questions, answers):
    correct=sum(1 for i,q in enumerate(questions) if answers.get(i)==q["correct_answer"])
    total=len(questions); return {"correct":correct,"total":total,"percentage":round(correct/total*100,1) if total else 0,"unanswered":total-len(answers)}
def mistake_from_question(q,selected=None):
    return {"question":q["question"],"options":q["options"],"selected_answer":selected or "","correct_answer":q["correct_answer"],"explanation":q.get("explanation",""),"topic":q.get("topic","General"),"difficulty":q.get("difficulty","Medium"),"source_ref":q.get("source_ref",""),"status":"Needs More Practice","created_at":datetime.now(timezone.utc).isoformat()}
def chunk_text(text,size=7000,overlap=500):
    text=text.strip(); out=[]; start=0
    while start<len(text):
        end=min(len(text),start+size); out.append(text[start:end])
        if end==len(text): break
        start=end-overlap
    return out
