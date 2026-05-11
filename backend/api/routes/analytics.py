from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from services.analytics import get_buffer_data, get_heatmap, get_province_data


router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/heatmap/{species}")
def get_heatmap_route(
    species: str,
    db: Session = Depends(get_db),
    year_from: int | None = Query(None, description="Start year (inclusive)"),
    year_to: int | None = Query(None, description="End year (inclusive)"),
    include_unknown: bool = Query(True, description="Whether to include records with unknown year"),
):
    return get_heatmap(species, db, year_from=year_from, year_to=year_to, include_unknown=include_unknown)


@router.get("/province-data/{species}")
def get_province_data_route(
    species: str,
    level: str = Query("province", description="行政区层级：province、city、district"),
    db: Session = Depends(get_db),
    year_from: int | None = Query(None, description="Start year (inclusive)"),
    year_to: int | None = Query(None, description="End year (inclusive)"),
    include_unknown: bool = Query(True, description="Whether to include records with unknown year"),
):
    return get_province_data(species, db, level=level, year_from=year_from, year_to=year_to, include_unknown=include_unknown)


@router.get("/buffer-data/{species}")
def get_buffer_data_route(
    species: str,
    radius_meters: float = Query(1000, ge=1, le=500000, description="缓冲区半径，单位米"),
    db: Session = Depends(get_db),
    year_from: int | None = Query(None, description="Start year (inclusive)"),
    year_to: int | None = Query(None, description="End year (inclusive)"),
    include_unknown: bool = Query(True, description="Whether to include records with unknown year"),
):
    return get_buffer_data(
        species,
        db,
        radius_meters=radius_meters,
        year_from=year_from,
        year_to=year_to,
        include_unknown=include_unknown,
    )