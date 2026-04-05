"""
SQLite 数据库配置和模型定义

支持多用户并发读取，单点写入（由于SQLite特性）
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List
from datetime import datetime
import threading

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import get_settings

# 数据库路径
DATABASE_URL = "sqlite:///" + str(get_settings().data_dir / "species.db")

# SQLAlchemy 引擎和会话工厂
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},  # 30秒超时
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 用于同步写入操作的线程锁
_write_lock = threading.RLock()


class SpeciesDistribution(Base):
    """物种分布数据模型"""
    __tablename__ = "species_distribution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    species_label = Column(String(100), nullable=False, index=True)
    scientific_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    province = Column(String(50), nullable=True)
    region_code = Column(String(10), nullable=True)
    date = Column(DateTime, nullable=True)
    dataset = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
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
    """用户上报的位置记录"""
    __tablename__ = "location_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    species = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(255), nullable=False)
    date = Column(String(10), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "species": self.species,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "date": self.date,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print(f"✓ 数据库初始化完成: {DATABASE_URL}")


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_sync():
    """同步方式获取数据库会话（带写锁）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_write_lock():
    """获取写操作锁，确保数据一致性"""
    _write_lock.acquire()
    try:
        yield
    finally:
        _write_lock.release()


# 数据库操作函数

def get_species_list(db: Session) -> List[str]:
    """
    获取所有物种名称列表

    Returns:
        排序后的物种名称列表
    """
    results = db.query(SpeciesDistribution.species_label).distinct().all()
    return sorted([r[0] for r in results])


def get_locations_by_species(db: Session, species: str, limit: int = 1000) -> List[dict]:
    """
    获取某个物种的所有分布位置

    Args:
        db: 数据库会话
        species: 物种名称
        limit: 返回记录的最大数量

    Returns:
        位置列表 [{"latitude": ..., "longitude": ..., "location_name": ...}, ...]
    """
    results = (
        db.query(SpeciesDistribution)
        .filter(SpeciesDistribution.species_label == species)
        .limit(limit)
        .all()
    )

    return [
        {
            "latitude": r.latitude,
            "longitude": r.longitude,
            "location_name": r.province or f"{r.latitude:.4f}, {r.longitude:.4f}",
        }
        for r in results
    ]


def add_location_record(
    db: Session,
    species: str,
    latitude: float,
    longitude: float,
    location_name: str,
    date: Optional[str] = None,
) -> LocationRecord:
    """
    添加用户上报的位置记录

    Args:
        db: 数据库会话
        species: 物种名称
        latitude: 纬度
        longitude: 经度
        location_name: 位置名称
        date: 日期（格式：YYYY-MM-DD）

    Returns:
        新创建的记录对象
    """
    with get_write_lock():
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


def get_all_records(db: Session) -> List[dict]:
    """获取所有用户上报的记录"""
    results = db.query(LocationRecord).all()
    return [r.to_dict() for r in results]


def bulk_insert_species_data(data: List[dict]) -> int:
    """
    批量插入物种分布数据

    Args:
        data: 数据列表，每项包含: species_label, scientific_name, latitude, longitude, ...

    Returns:
        插入的记录数
    """
    with get_write_lock():
        db = SessionLocal()
        try:
            count = 0
            for item in data:
                if item["latitude"] is None or item["longitude"] is None:
                    continue

                # 检查坐标范围有效性
                if not (-90 <= item["latitude"] <= 90 and -180 <= item["longitude"] <= 180):
                    continue

                record = SpeciesDistribution(
                    species_label=item.get("species_label"),
                    scientific_name=item.get("scientific_name"),
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    province=item.get("province"),
                    region_code=item.get("region_code"),
                    date=_parse_date(item.get("date")),
                    dataset=item.get("dataset"),
                    year=item.get("year"),
                )
                db.add(record)
                count += 1

            db.commit()
            return count
        finally:
            db.close()


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def get_db_stats(db: Session) -> dict:
    """获取数据库统计信息"""
    total_species = db.query(SpeciesDistribution).count()
    species_count = db.query(SpeciesDistribution.species_label).distinct().count()
    user_records = db.query(LocationRecord).count()

    return {
        "total_species_records": total_species,
        "unique_species": species_count,
        "user_records": user_records,
    }
