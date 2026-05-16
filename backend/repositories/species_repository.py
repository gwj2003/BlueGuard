from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, or_, case
from sqlalchemy.orm import Session

from models import SpeciesDistribution


def list_species_names(db: Session) -> list[str]:
    results = db.query(SpeciesDistribution.species_label).distinct().all()
    return sorted([row[0] for row in results])


def list_locations_by_species(
    db: Session,
    species: str,
    limit: int | None = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    include_unknown: bool = True,
) -> list[dict]:
    """返回指定物种的位置信息，支持按年份范围过滤并可选择是否包含未知年份记录。

    参数:
      - `limit`: 可选，限制返回条数。
      - `year_from`, `year_to`: 可选，按 `year` 字段做闭区间过滤。
      - `include_unknown`: 若为 True，则在有 year_from/year_to 过滤时仍包含 year 为 NULL 的记录；若为 False 则排除 year 为 NULL。
    """
    query = db.query(SpeciesDistribution).filter(SpeciesDistribution.species_label == species)

    # apply year filters
    has_year_filter = year_from is not None or year_to is not None
    if not has_year_filter:
        # no range provided
        if include_unknown is False:
            query = query.filter(SpeciesDistribution.year != None)
    else:
        clauses = []
        if year_from is not None:
            clauses.append(SpeciesDistribution.year >= int(year_from))
        if year_to is not None:
            clauses.append(SpeciesDistribution.year <= int(year_to))
        range_filter = and_(*clauses) if clauses else None
        if include_unknown:
            if range_filter is not None:
                query = query.filter(or_(range_filter, SpeciesDistribution.year == None))
        else:
            if range_filter is not None:
                query = query.filter(range_filter)

    if limit is not None:
        query = query.limit(limit)
    results = query.all()

    return [
        {
            "latitude": row.latitude,
            "longitude": row.longitude,
            "location_name": row.province or f"{row.latitude:.4f}, {row.longitude:.4f}",
            "year": row.year,
            "province": row.province,
            "city": row.city,
            "district": row.district,
        }
        for row in results
    ]


def count_locations_by_admin_field(
    db: Session,
    species: str,
    admin_field: str,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    include_unknown: bool = True,
) -> dict[str, int]:
    if admin_field not in {"province", "city", "district"}:
        return {}
    # For Hong Kong, Macau and Taiwan we always aggregate at province level
    SPECIAL_PROVINCES = {"台湾省", "香港特别行政区", "澳门特别行政区"}

    if admin_field == "province":
        field = getattr(SpeciesDistribution, "province")
        group_expr = field
    else:
        # group by province for special provinces, otherwise by the requested field
        field = getattr(SpeciesDistribution, admin_field)
        group_expr = case(
            (SpeciesDistribution.province.in_(list(SPECIAL_PROVINCES)), SpeciesDistribution.province),
            else_=field,
        )

    query = db.query(group_expr, func.count(SpeciesDistribution.id)).filter(
        SpeciesDistribution.species_label == species,
        group_expr != None,
        group_expr != "",
    )
    query = _apply_year_filters(query, year_from, year_to, include_unknown)
    rows = query.group_by(group_expr).all()
    result: dict[str, int] = {}
    for value, count in rows:
        if value is None:
            continue
        s = str(value).strip()
        if not s:
            continue
        result[s] = int(count)
    return result


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
                city=item.get("city"),
                district=item.get("district"),
                region_code=item.get("region_code"),
                date=_parse_date(item.get("date")),
                dataset=item.get("dataset"),
                year=item.get("year"),
            )
        )
        count += 1
    db.commit()
    return count


def _apply_year_filters(query, year_from: Optional[int], year_to: Optional[int], include_unknown: bool):
    has_year_filter = year_from is not None or year_to is not None
    if not has_year_filter:
        if include_unknown is False:
            query = query.filter(SpeciesDistribution.year != None)
        return query

    clauses = []
    if year_from is not None:
        clauses.append(SpeciesDistribution.year >= int(year_from))
    if year_to is not None:
        clauses.append(SpeciesDistribution.year <= int(year_to))
    range_filter = and_(*clauses) if clauses else None
    if include_unknown:
        if range_filter is not None:
            query = query.filter(or_(range_filter, SpeciesDistribution.year == None))
    else:
        if range_filter is not None:
            query = query.filter(range_filter)
    return query


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None
