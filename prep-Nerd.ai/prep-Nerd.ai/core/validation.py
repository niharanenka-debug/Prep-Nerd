from typing import Any
from pydantic import BaseModel, Field, field_validator
class Question(BaseModel):
    question:str
    options:dict[str,str]
    correct_answer:str
    explanation:str
    hint:str|None=None
    topic:str="General"
    difficulty:str="Medium"
    source_ref:str=""
    @field_validator("correct_answer")
    @classmethod
    def valid_answer(cls,v):
        if v not in "ABCD": raise ValueError("correct_answer must be A, B, C, or D")
        return v
    @field_validator("options")
    @classmethod
    def four_options(cls,v):
        if set(v)!=set("ABCD"): raise ValueError("options must contain A-D")
        return v
class QuizPayload(BaseModel):
    questions:list[Question]=Field(min_length=1,max_length=25)
    @field_validator("questions")
    @classmethod
    def no_dupes(cls,v):
        if len({q.question.strip().lower() for q in v})!=len(v): raise ValueError("duplicate questions")
        return v
class Flashcard(BaseModel):
    front:str; back:str; rating:str="Needs Review"; source_ref:str=""
    @field_validator("rating")
    @classmethod
    def valid_rating(cls,v):
        if v not in {"Easy","Needs Review","Difficult"}: raise ValueError("invalid rating")
        return v
