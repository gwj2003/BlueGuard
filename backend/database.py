"""Database bootstrap and compatibility helpers."""

from __future__ import annotations

import csv
import threading
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import get_settings
from models import Base
from repositories.records_repository import (
    create_location_record as repo_create_location_record,
    list_location_records as repo_list_location_records,
)
from repositories.species_repository import (
    bulk_insert_species_data as repo_bulk_insert_species_data,
    list_locations_by_species as repo_list_locations_by_species,
    list_species_names as repo_list_species_names,
)
from repositories.stats_repository import get_db_stats as repo_get_db_stats


DATABASE_URL = "sqlite:///" + str(get_settings().runtime_dir / "species.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_write_lock = threading.RLock()


def init_db() -> None:
    get_settings().runtime_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"数据库初始化完成: {DATABASE_URL}")


def ensure_seed_data() -> int:
    """Seed species data from CSV files when the database is empty."""
    init_db()

    db = SessionLocal()
    try:
        existing_species = repo_list_species_names(db)
    finally:
        db.close()

    if existing_species:
        return 0

    settings = get_settings()
    gbif_dir = settings.data_dir / "gbif_results"
    if not gbif_dir.exists():
        print(f"[Startup][WARN] GBIF 数据目录不存在，跳过自动迁移: {gbif_dir}")
        return 0

    csv_files = sorted(gbif_dir.glob("*.csv"))
    if not csv_files:
        print(f"[Startup][WARN] 未找到 GBIF CSV 文件，跳过自动迁移: {gbif_dir}")
        return 0

    total_imported = 0
    print(f"[Startup] 数据库为空，开始自动迁移 {len(csv_files)} 个 CSV 文件...")
    for csv_file in csv_files:
        species_name = csv_file.stem
        rows: list[dict] = []

        with csv_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(
                    {
                        "species_label": row.get("species_label") or species_name,
                        "scientific_name": row.get("gbif_scientific_name"),
                        "latitude": _safe_float(row.get("lat")),
                        "longitude": _safe_float(row.get("lng")),
                        "province": row.get("province"),
                        "region_code": row.get("region_code"),
                        "date": row.get("date"),
                        "dataset": row.get("dataset"),
                        "year": _safe_int(row.get("year")),
                    }
                )

        imported = bulk_insert_species_data(rows)
        total_imported += imported
        print(f"[Startup] {csv_file.name} -> {imported} 条")

    print(f"[Startup] 自动迁移完成，总计导入 {total_imported} 条记录")
    return total_imported


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_sync():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_write_lock():
    _write_lock.acquire()
    try:
        yield
    finally:
        _write_lock.release()


def get_species_list(db: Session) -> list[str]:
    return repo_list_species_names(db)


def get_locations_by_species(db: Session, species: str, limit: int = 1000) -> list[dict]:
    return repo_list_locations_by_species(db, species, limit=limit)


def add_location_record(
    db: Session,
    species: str,
    latitude: float,
    longitude: float,
    location_name: str,
    date: str | None = None,
):
    with get_write_lock():
        return repo_create_location_record(
            db,
            species=species,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            date=date,
        )


def get_all_records(db: Session) -> list[dict]:
    return repo_list_location_records(db)


def bulk_insert_species_data(rows: list[dict]) -> int:
    with get_write_lock():
        db = SessionLocal()
        try:
            return repo_bulk_insert_species_data(db, rows)
        finally:
            db.close()


def get_db_stats(db: Session) -> dict:
    return repo_get_db_stats(db)


def _safe_float(value) -> float | None:
    try:
        return float(value) if value else None
    except (ValueError, TypeError):
        return None


def _safe_int(value) -> int | None:
    try:
        return int(value) if value else None
    except (ValueError, TypeError):
        return None
