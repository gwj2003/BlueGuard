from sqlalchemy.orm import Session

from models import LocationRecord, SpeciesDistribution


def get_db_stats(db: Session) -> dict:
    return {
        "total_species_records": db.query(SpeciesDistribution).count(),
        "unique_species": db.query(SpeciesDistribution.species_label).distinct().count(),
        "user_records": db.query(LocationRecord).count(),
    }
