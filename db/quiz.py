from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
import re
from datetime import datetime

from database import get_db
from models import Quiz, Question, Answer, QuizResult, Choices
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

# Route to create a question
@router.post("/questions/create/{paper_code}")
def create_question(
    paper_code: str,
    data: dict,
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    # Get the quiz by paper code
    quiz = db.query(Quiz).filter(Quiz.paperCode == paper_code).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Verify the user is the creator of the quiz
    if quiz.created_by != access_token:
        raise HTTPException(status_code=403, detail="Not authorized to add questions to this quiz")

    # Create the question
    question = Question(
        quiz_id=quiz.id,
        question_text=data["questionText"],
        question_type=data["questionType"],
        correct_answer=data["correctAnswer"],
        case_sensitive=data.get("caseSensitive", False),
        points=data["points"]
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    # If it's a multiple choice question, create the choices
    if data["questionType"] == "multiple-choice" and "options" in data:
        for i, option_text in enumerate(data["options"]):
            choice = Choices(
                question_id=question.id,
                choice_text=option_text,
                is_correct=(str(i) == data["correctAnswer"])
            )
            db.add(choice)
        db.commit()

    return {"message": "Question created successfully", "question_id": question.id}

# Route to fetch questions for a quiz
@router.get("/questions/{paper_code}")
def get_quiz_questions(
    paper_code: str,
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    # Get the quiz by paper code
    quiz = db.query(Quiz).filter(Quiz.paperCode == paper_code).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Verify the user is the creator of the quiz
    if quiz.created_by != access_token:
        raise HTTPException(status_code=403, detail="Not authorized to view questions for this quiz")
    
    # Get all questions for the quiz
    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    
    # Format the response
    formatted_questions = []
    for question in questions:
        question_data = {
            "id": question.id,
            "questionText": question.question_text,
            "questionType": question.question_type,
            "correctAnswer": question.correct_answer,
            "caseSensitive": question.case_sensitive,
            "points": question.points
        }
        
        # If it's a multiple choice question, include the options
        if question.question_type == "multiple-choice":
            choices = db.query(Choices).filter(Choices.question_id == question.id).all()
            question_data["options"] = [choice.choice_text for choice in choices]
        
        formatted_questions.append(question_data)
    
    return formatted_questions

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

# Route to delete a question
@router.delete("/questions/{paper_code}/{question_id}")
def delete_question(
    paper_code: str,
    question_id: int,
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    # Get the quiz by paper code
    quiz = db.query(Quiz).filter(Quiz.paperCode == paper_code).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Verify the user is the creator of the quiz
    if quiz.created_by != access_token:
        raise HTTPException(status_code=403, detail="Not authorized to delete questions from this quiz")
    
    # Get the question
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz.id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Delete the question (cascade will handle related choices)
    db.delete(question)
    db.commit()
    
    return {"message": "Question deleted successfully"}

# Route to update a question
@router.put("/questions/{paper_code}/{question_id}")
def update_question(
    paper_code: str,
    question_id: int,
    data: dict,
    db: Session = Depends(get_db),
    access_token: int = Depends(get_user_id_from_auth)
):
    # Get the quiz by paper code
    quiz = db.query(Quiz).filter(Quiz.paperCode == paper_code).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Verify the user is the creator of the quiz
    if quiz.created_by != access_token:
        raise HTTPException(status_code=403, detail="Not authorized to update questions in this quiz")
    
    # Get the question
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz.id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Update the question
    question.question_text = data["questionText"]
    question.question_type = data["questionType"]
    question.correct_answer = data["correctAnswer"]
    question.case_sensitive = data.get("caseSensitive", False)
    question.points = data["points"]
    
    # If it's a multiple choice question, update the choices
    if data["questionType"] == "multiple-choice" and "options" in data:
        # Delete existing choices
        db.query(Choices).filter(Choices.question_id == question.id).delete()
        
        # Create new choices
        for i, option_text in enumerate(data["options"]):
            choice = Choices(
                question_id=question.id,
                choice_text=option_text,
                is_correct=(str(i) == data["correctAnswer"])
            )
            db.add(choice)
    
    db.commit()
    return {"message": "Question updated successfully"}