from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models import LocationRecord


def create_location_record(
    db: Session,
    *,
    species: str,
    latitude: float,
    longitude: float,
    location_name: str,
    date: str | None = None,
) -> LocationRecord:
    record = LocationRecord(
        species=species,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        date=date or datetime.now().strftime("%Y-%m-%d"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_location_records(db: Session) -> list[dict]:
    return [row.to_dict() for row in db.query(LocationRecord).all()]
