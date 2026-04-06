from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SpeciesDistribution(Base):
    __tablename__ = "species_distribution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species_label: Mapped[str] = mapped_column(String(100), index=True)
    scientific_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "species_label": self.species_label,
            "scientific_name": self.scientific_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "province": self.province,
            "region_code": self.region_code,
            "date": self.date.isoformat() if self.date else None,
            "dataset": self.dataset,
            "year": self.year,
        }


class LocationRecord(Base):
    __tablename__ = "location_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species: Mapped[str] = mapped_column(String(100), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_name: Mapped[str] = mapped_column(String(255))
    date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "species": self.species,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "date": self.date,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
