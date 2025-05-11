# db/schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class AnswerCreate(BaseModel):
    text: str
    is_correct: bool

class QuestionCreate(BaseModel):
    text: str
    answers: List[AnswerCreate]

class QuizCreate(BaseModel):
    title: str
    description: str
    startTime: str
    endTime: str
    timer: int
    forwardOnly: bool
    paperCode: str
    created_by: int
    created_at: str

class QuizSubmission(BaseModel):
    quiz_id: int
    answers: Dict[int, int]  # question_id: selected_answer_id

class QuizResultResponse(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    score: float
    total: int
    submitted_at: str

    class Config:
        orm_mode = True
