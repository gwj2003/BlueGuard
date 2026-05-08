from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.analytics import get_heatmap,  get_province_data


router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/heatmap/{species}")
def get_heatmap_route(species: str, db: Session = Depends(get_db)):
    return get_heatmap(species, db)


@router.get("/province-data/{species}")
def get_province_data_route(species: str, db: Session = Depends(get_db)):
    return get_province_data(species, db)