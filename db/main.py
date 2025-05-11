from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models

from auth import router as auth_router
from quiz import router as quiz_router  # <-- ADD THIS

app = FastAPI()

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "QuizSecure API is up!"}

# Include routers
app.include_router(auth_router, prefix="/api/auth")
#app.include_router(quiz_router, prefix="/api/quiz") 
app.include_router(quiz_router, prefix="/api/quizzes")