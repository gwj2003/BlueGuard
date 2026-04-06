from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.qa import QuestionRequest
from services.qa import ask_question, get_suggestions


router = APIRouter(prefix="/api", tags=["qa"])


@router.post("/qa")
def qa_question(request: QuestionRequest, db: Session = Depends(get_db)):
    return ask_question(request.question, db)


@router.get("/qa/suggestions/{species}")
def qa_suggestions(species: str):
    return get_suggestions(species)
