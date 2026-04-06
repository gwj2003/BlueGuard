from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models import SpeciesDistribution


def list_species_names(db: Session) -> list[str]:
    results = db.query(SpeciesDistribution.species_label).distinct().all()
    return sorted([row[0] for row in results])


def list_locations_by_species(db: Session, species: str, limit: int = 1000) -> list[dict]:
    results = (
        db.query(SpeciesDistribution)
        .filter(SpeciesDistribution.species_label == species)
        .limit(limit)
        .all()
    )
    return [
        {
            "latitude": row.latitude,
            "longitude": row.longitude,
            "location_name": row.province or f"{row.latitude:.4f}, {row.longitude:.4f}",
        }
        for row in results
    ]


def bulk_insert_species_data(db: Session, rows: list[dict]) -> int:
    count = 0
    for item in rows:
        latitude = item.get("latitude")
        longitude = item.get("longitude")
        if latitude is None or longitude is None:
            continue
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue

        db.add(
            SpeciesDistribution(
                species_label=item.get("species_label"),
                scientific_name=item.get("scientific_name"),
                latitude=float(latitude),
                longitude=float(longitude),
                province=item.get("province"),
                region_code=item.get("region_code"),
                date=_parse_date(item.get("date")),
                dataset=item.get("dataset"),
                year=item.get("year"),
            )
        )
        count += 1
    db.commit()
    return count


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None
