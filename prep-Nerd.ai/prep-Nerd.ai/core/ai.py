import json
from .config import MODEL, api_key
from .logic import chunk_text

class AIError(RuntimeError):
    pass

class GeminiService:
    def __init__(self, model=MODEL):
        self.model = model
        self.client = None
        key = api_key()
        if key:
            try:
                from google import genai
                self.client = genai.Client(api_key=key)
            except Exception as exc:
                raise AIError(f"Gemini SDK initialization failed: {exc}")

    def generate(self, prompt):
        if not self.client:
            raise AIError("Add GEMINI_API_KEY in .env or Streamlit secrets to use AI features.")
        try:
            response = self.client.models.generate_content(model=self.model, contents=prompt)
            text = getattr(response, "text", None)
            if not text:
                raise AIError("Gemini returned an empty response")
            return text
        except Exception as exc:
            raise AIError(f"Gemini request failed: {exc}")

    def json(self, prompt):
        text = self.generate(prompt).strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return json.loads(text)
        except Exception as exc:
            raise AIError(f"Gemini returned invalid JSON: {exc}")

    def analyze(self, task, content, depth="Standard"):
        chunks = chunk_text(content)
        cap = {"Quick": 1, "Standard": 3, "Deep": 6,
               "Exhaustive": len(chunks), "Automatic": min(3, len(chunks))}.get(depth, 3)
        selected = chunks[:max(1, cap)]
        partial = len(selected) < len(chunks)
        prompt = (
            f"You are prep-Nerd.ai, a careful study assistant. Analysis depth: {depth}. "
            f"Return accurate, useful output for this task: {task}.\n"
            f"Coverage note: {'partial; say so explicitly' if partial else 'complete'}.\n"
            "SOURCE:\n" + "\n---\n".join(selected)
        )
        return self.generate(prompt)
