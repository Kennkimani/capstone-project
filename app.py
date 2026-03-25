from fastapi import FastAPI
from pydantic import BaseModel
from database import get_connection
from ai_service import generate_feedback,generate_question
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
import json
import re

def clean_answer(ans):
    ans = str(ans)
    ans = ans.replace("\\boxed{", "").replace("}", "")
    ans = re.sub(r"[^\d\.\-]", "", ans)

    return ans.strip()



app = FastAPI(title='Learning API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or your specific frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnswerRequest(BaseModel):
    student_id: int
    topic: str
    question: str
    student_answer: str
    correct_answers: str
    time_taken: float

class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class QuestionRequest(BaseModel):
    topic: str
    difficulty: Difficulty

@app.get("/")
def home():
    return {"message": "Adaptive Learning API is running"}

@app.get("/test-db")
async def test_db():
    conn = await get_connection()
    rows = await conn.fetch("SELECT * FROM capstone.students")
    await conn.close()
    return rows


@app.post("/generate-question")
async def generate_quiz_question(data: QuestionRequest):

    raw_question = await generate_question(
        data.topic,
        data.difficulty
    )
    
    try:
        # If AI returns a string with markdown (```json ... ```), strip it
        clean_raw = raw_question.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_raw)
        question_text = parsed.get("question", "No question generated")
        correct_answer = parsed.get("correct_answer", "No answer provided")
    except Exception as e:
        print(f"Parsing error: {e}")
        question_text = raw_question
        correct_answer = "Check AI response"

    return {
        "question": question_text,
        "correct_answer": correct_answer
    }



@app.post("/submit-answer")
async def submit_answer(data: AnswerRequest):

    correct = clean_answer(data.student_answer) == clean_answer(data.correct_answers)
    feedback = await generate_feedback(
        data.topic,
        data.question,
        data.student_answer,
        data.correct_answers,
        correct
    )

    conn = await get_connection()

    try:
        # Added 'capstone.' schema prefix to table name
        await conn.execute("""
            INSERT INTO capstone.Quiz_results 
            (student_id, topic, question, student_answer, correct_answers, 
             is_correct, time_taken, ai_response)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 
        data.student_id, data.topic, data.question, data.student_answer, 
        data.correct_answers, correct, data.time_taken, feedback)
    finally:
        await conn.close()

    return {"correct": correct, "feedback": feedback}

@app.get("/struggling-students")
async def struggling_students(threshold: float = 0.6):

    conn = await get_connection()

    rows = await conn.fetch("""
        SELECT s.name,q.student_id,
        AVG(CASE WHEN is_correct THEN 1 ELSE 0 END) as avg_score
        FROM Quiz_results q
        JOIN students s ON q.student_id = s.student_id
        GROUP BY q.student_id,s.name
        HAVING AVG(CASE WHEN q.is_correct THEN 1 ELSE 0 END) < $1
    """, threshold)

    await conn.close()

    return rows