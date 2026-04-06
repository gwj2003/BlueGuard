from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.admin import get_health_status


router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    return get_health_status(db)
