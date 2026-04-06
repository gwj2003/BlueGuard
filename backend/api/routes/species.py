from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.species import get_species_info, list_species, list_species_locations


router = APIRouter(prefix="/api", tags=["species"])


@router.get("/species")
def list_species_route(db: Session = Depends(get_db)):
    return list_species(db)


@router.get("/species/{species}")
def get_species_info_route(species: str, db: Session = Depends(get_db)):
    return get_species_info(species, db)


@router.get("/locations/{species}")
def get_locations_route(species: str, db: Session = Depends(get_db)):
    return list_species_locations(species, db)
