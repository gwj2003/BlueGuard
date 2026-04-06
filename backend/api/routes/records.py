from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.records import LocationRecordCreate
from services.records import create_location_record, list_location_records


router = APIRouter(prefix="/api", tags=["records"])


@router.post("/record/location")
def record_location(record: LocationRecordCreate, db: Session = Depends(get_db)):
    try:
        return create_location_record(
            db,
            species=record.species,
            latitude=record.latitude,
            longitude=record.longitude,
            location_name=record.location_name,
            date=record.date,
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Record Error: {exc}")
        raise HTTPException(status_code=500, detail=f"保存失败: {exc}") from exc


@router.get("/records")
def get_records(db: Session = Depends(get_db)):
    return list_location_records(db)
