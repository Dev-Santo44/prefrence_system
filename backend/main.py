"""
FastAPI Main Application - AI-Driven Personal Preference Identifier
Exposes endpoints for authentication, survey management, and results.
"""

import sys
import os

# Allow importing from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict

from backend.auth import hash_password, verify_password, create_access_token, decode_token
from backend.database import execute_query
from models.ocean_scorer import score_and_recommend

app = FastAPI(
    title="AI-Driven Personal Preference Identifier",
    description="Analyzes user behavioral data using NLP and OCEAN model to generate preference profiles.",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SurveySubmitRequest(BaseModel):
    # Likert answers grouped by trait: {"Openness": [4,5,3,4,5], ...}
    likert_answers: Dict[str, List[float]]
    # Optional open-ended text answers
    open_texts: Optional[List[str]] = None


# ─── Dependency: Current User ─────────────────────────────────────────────────

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ─── Auth Endpoints ───────────────────────────────────────────────────────────

@app.post("/auth/register", status_code=201, summary="Register a new user")
def register(request: RegisterRequest):
    # Check if email already exists
    existing = execute_query(
        "SELECT user_id FROM users WHERE email = %s", (request.email,), fetch=True
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed = hash_password(request.password)
    user_id = execute_query(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        (request.name, request.email, hashed, request.role or "user"),
    )
    token = create_access_token({"sub": str(user_id)})
    return {"message": "Registration successful", "user_id": user_id, "access_token": token}


@app.post("/auth/login", summary="Login and receive JWT token")
def login(request: LoginRequest):
    rows = execute_query(
        "SELECT user_id, password, name, role FROM users WHERE email = %s",
        (request.email,),
        fetch=True,
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user = rows[0]
    if not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": str(user["user_id"])})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "name": user["name"],
        "role": user["role"],
    }


# ─── Survey Endpoints ─────────────────────────────────────────────────────────

@app.get("/survey/questions", summary="Get all survey questions")
def get_questions():
    questions = execute_query(
        "SELECT q_id, question_text, category FROM survey_questions ORDER BY category, q_id",
        fetch=True,
    )
    return {"questions": questions}


@app.post("/survey/submit", summary="Submit survey answers and compute OCEAN scores")
def submit_survey(
    request: SurveySubmitRequest,
    user_id: int = Depends(get_current_user),
):
    # Save raw Likert responses
    traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
    for trait, answers in request.likert_answers.items():
        if trait not in traits:
            continue
        # Retrieve q_ids for this trait
        qs = execute_query(
            "SELECT q_id FROM survey_questions WHERE category = %s ORDER BY q_id",
            (trait,),
            fetch=True,
        )
        for i, q in enumerate(qs):
            if i < len(answers):
                execute_query(
                    "INSERT INTO responses (user_id, q_id, answer) VALUES (%s, %s, %s)",
                    (user_id, q["q_id"], str(answers[i])),
                )

    # Compute OCEAN scores
    result = score_and_recommend(request.likert_answers, request.open_texts)

    # Save preference results (upsert: delete old, insert new)
    execute_query("DELETE FROM preference_results WHERE user_id = %s", (user_id,))
    execute_query(
        """INSERT INTO preference_results
           (user_id, openness_score, conscientiousness_score, extraversion_score,
            agreeableness_score, neuroticism_score, recommendations)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            user_id,
            result["openness"],
            result["conscientiousness"],
            result["extraversion"],
            result["agreeableness"],
            result["neuroticism"],
            result["recommendations"],
        ),
    )

    return {"message": "Survey submitted successfully", "results": result}


@app.get("/results/{user_id}", summary="Get OCEAN results for a user")
def get_results(user_id: int, current_user: int = Depends(get_current_user)):
    # Allow users to see only their own results; admins can see any
    rows = execute_query(
        "SELECT role FROM users WHERE user_id = %s", (current_user,), fetch=True
    )
    if not rows:
        raise HTTPException(status_code=404, detail="User not found.")
    role = rows[0]["role"]

    if current_user != user_id and role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    result = execute_query(
        """SELECT openness_score, conscientiousness_score, extraversion_score,
                  agreeableness_score, neuroticism_score, recommendations
           FROM preference_results WHERE user_id = %s""",
        (user_id,),
        fetch=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="No results found for this user.")

    return {"user_id": user_id, "results": result[0]}


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok", "service": "AI Preference Identifier API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
