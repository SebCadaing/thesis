from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
import re

from database import get_db
from models import Quiz, Question, Answer, QuizResult
from schemas import QuizCreate, QuizSubmission, QuizResultResponse

router = APIRouter(tags=["Quiz"])

# Dependency to extract user ID from Authorization header
def get_user_id_from_auth(auth_header: str = Header(..., alias="Authorization")) -> int:
    match = re.match(r"Bearer (\d+)", auth_header)
    if not match:
        raise HTTPException(status_code=401, detail="Invalid token format")
    return int(match.group(1))

# Route to create a quiz
@router.post("/create")
def create_quiz(
    data: QuizCreate,
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    quiz = Quiz(
        title=data.title,
        description=data.description,
        created_by=access_token,
        created_at=data.created_at,
        paperCode=data.paperCode,
        startTime=data.startTime,
        endTime=data.endTime,
        timer=data.timer,
        forwardOnly=data.forwardOnly
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return {"message": "Quiz created successfully", "quiz_id": quiz.id}

# Route to fetch all quizzes
@router.get("/all")
def get_all_quizzes(
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    quizzes = db.query(Quiz).all()
    return quizzes

# Route to submit a quiz
@router.post("/submit")
def submit_quiz(
    data: QuizSubmission,
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    score = 0
    total_questions = len(data.answers)

    for question_id, selected_answer_id in data.answers.items():
        correct_answer = db.query(Answer).filter_by(question_id=question_id, is_correct=True).first()
        if correct_answer and correct_answer.id == selected_answer_id:
            score += 1

    result = QuizResult(
        user_id=access_token,
        quiz_id=data.quiz_id,
        score=score,
        total=total_questions
    )
    db.add(result)
    db.commit()

    return {"message": "Quiz submitted successfully", "score": score, "total": total_questions}

# Route to get quiz result
@router.get("/result/{quiz_id}", response_model=QuizResultResponse)
def get_result(
    quiz_id: int,
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    result = db.query(QuizResult).filter_by(user_id=access_token, quiz_id=quiz_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return result