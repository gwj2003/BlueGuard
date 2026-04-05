"""
FastAPI 应用 - 数据库集成辅助函数
"""

from sqlalchemy.orm import Session
from database import (
    get_species_list as db_get_species_list,
    get_locations_by_species as db_get_locations_by_species,
)
from fastapi import HTTPException


def get_all_species(db: Session) -> list:
    """从数据库获取所有物种"""
    return db_get_species_list(db)


def get_locations(species: str, db: Session) -> list:
    """从数据库获取物种位置"""
    locations = db_get_locations_by_species(db, species, limit=1000)

    if not locations:
        all_species = db_get_species_list(db)
        if species not in all_species:
            raise HTTPException(status_code=404, detail=f"物种 '{species}' 未找到")

    return locations


def resolve_species_name(raw: str, db: Session):
    """规范物种名称"""
    s = (raw or "").strip()
    if not s:
        return "", False

    names = db_get_species_list(db)

    if s in names:
        return s, True

    by_lower = {n.lower(): n for n in names}
    if s.lower() in by_lower:
        return by_lower[s.lower()], True

    return s, False
