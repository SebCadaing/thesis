from database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String)  # "student" or "teacher"
    password = Column(String)

    quizzes_created = relationship("Quiz", back_populates="creator", cascade="all, delete")
    submissions = relationship("Submission", back_populates="student", cascade="all, delete")
    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete")


class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(String)

    # New fields
    paperCode = Column(String, unique=True, index=True)
    startTime = Column(String)
    endTime = Column(String)
    timer = Column(Integer)  # e.g., duration in minutes
    forwardOnly = Column(Boolean, default=False)

    creator = relationship("User", back_populates="quizzes_created")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete")
    submissions = relationship("Submission", back_populates="quiz", cascade="all, delete")
    redemptions = relationship("RedeemedCode", back_populates="quiz", cascade="all, delete")
    results = relationship("QuizResult", back_populates="quiz", cascade="all, delete")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_text = Column(String)
    question_type = Column(String)  # "mcq" or "identification"
    correct_answer = Column(String)
    case_sensitive = Column(Boolean, default=False)
    points = Column(Float, default=1.0)


    quiz = relationship("Quiz", back_populates="questions")
    choices = relationship("Choices", back_populates="question", cascade="all, delete")
    answers = relationship("Answer", back_populates="question", cascade="all, delete")


class Choices(Base):
    __tablename__ = "choices"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    choice_text = Column(String)
    is_correct = Column(Boolean)

    question = relationship("Question", back_populates="choices")


class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    submitted_at = Column(String)
    score = Column(Float)
    

    quiz = relationship("Quiz", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete")
    redflag = relationship("RedFlag", back_populates="submission", cascade="all, delete")


class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_text = Column(String)

    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class RedFlag(Base):
    __tablename__ = "redflag"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    timestamp = Column(String)
    flag_type = Column(String)  # "no_face", "multiple_faces", "tab_switch"

    submission = relationship("Submission", back_populates="redflag")


class RedeemedCode(Base):
    __tablename__ = "redeemed_codes"

    id = Column(Integer, primary_key=True, index=True)
    paperCode = Column(String, ForeignKey("quizzes.paperCode"))
    student_id = Column(Integer, ForeignKey("users.id"))
    redeemed_at = Column(String)

    quiz = relationship("Quiz", back_populates="redemptions")


class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    score = Column(Float)
    total = Column(Integer)
    submitted_at = Column(String, default=lambda: datetime.now().isoformat())

    user = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz", back_populates="results")