from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import pandas as pd
from fastapi import HTTPException
from shapely.geometry import MultiPolygon, Point, Polygon, mapping, shape
from shapely.ops import unary_union
from sqlalchemy.orm import Session

from config import get_settings
from domain.geo_data import get_china_gdf, get_china_geojson
from database import get_data_version
from repositories.species_repository import count_locations_by_admin_field, list_locations_by_species


_ADMIN_AREA_CACHE: dict[tuple[str, str, int], dict] = {}


def preload_admin_geojson_cache(levels: tuple[str, ...] = ("province", "city", "district")) -> dict[str, bool]:
    """Warm admin-area GeoJSON caches so the first map render avoids file parsing."""
    result: dict[str, bool] = {}
    for level in levels:
        normalized_level = _normalize_admin_level(level)
        result[normalized_level] = _load_admin_geojson(normalized_level) is not None
    return result


def get_heatmap(
    species: str,
    db: Session,
    year_from: int | None = None,
    year_to: int | None = None,
    include_unknown: bool = True,
) -> dict[str, list[list[float]]]:
    points: list[list[float]] = []
    for location in list_locations_by_species(db, species, None, year_from, year_to, include_unknown):
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is not None and lon is not None:
            points.append([lat, lon, 1.0])
    return {"points": points}


def get_province_data(
    species: str,
    db: Session,
    level: str = "province",
    year_from: int | None = None,
    year_to: int | None = None,
    include_unknown: bool = True,
) -> dict:
    normalized_level = _normalize_admin_level(level)
    return _get_admin_area_data_cached(species, normalized_level, get_data_version(), db, year_from, year_to, include_unknown)


def get_admin_area_data(
    species: str,
    db: Session,
    level: str = "province",
    year_from: int | None = None,
    year_to: int | None = None,
    include_unknown: bool = True,
) -> dict:
    normalized_level = _normalize_admin_level(level)
    return _get_admin_area_data_cached(species, normalized_level, get_data_version(), db, year_from, year_to, include_unknown)


def _get_admin_area_data_cached(
    species: str,
    normalized_level: str,
    data_version: int,
    db: Session,
    year_from: int | None = None,
    year_to: int | None = None,
    include_unknown: bool = True,
) -> dict:
    cache_key = (species, normalized_level, data_version, year_from, year_to, include_unknown)
    cached = _ADMIN_AREA_CACHE.get(cache_key)
    if cached is not None:
        return cached

    result = _build_admin_area_data(species, db, normalized_level, year_from, year_to, include_unknown)
    _ADMIN_AREA_CACHE[cache_key] = result
    return result


def _build_admin_area_data(
    species: str,
    db: Session,
    normalized_level: str,
    year_from: int | None = None,
    year_to: int | None = None,
    include_unknown: bool = True,
) -> dict:
    admin_geojson = _load_admin_geojson(normalized_level)
    if not admin_geojson:
        raise HTTPException(
            status_code=404,
            detail=f"未找到 {normalized_level} 级行政区 GeoJSON，请先添加 AreaCity_ok_geo 数据。",
        )

    gdf_map = gpd.GeoDataFrame.from_features(admin_geojson.get("features", []))
    if not gdf_map.empty:
        gdf_map.set_crs(epsg=4326, inplace=True)

    dist = count_locations_by_admin_field(db, species, normalized_level, year_from, year_to, include_unknown)
    locations = None
    province_counts = count_locations_by_admin_field(db, species, "province", year_from, year_to, include_unknown)
    special_region_features = _build_special_region_fallback_features(province_geojson=admin_geojson if normalized_level == "province" else _load_admin_geojson("province"), province_counts=province_counts, normalized_level=normalized_level)

    if not dist:
        locations = list_locations_by_species(db, species, None, year_from, year_to, include_unknown)
        if not gdf_map.empty and locations:
            locations = [loc for loc in locations if not _is_special_region_province(loc.get("province"))]
        if not gdf_map.empty and locations:
            df = pd.DataFrame(locations)
            if not df.empty and "longitude" in df.columns and "latitude" in df.columns:
                geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
                points_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
                joined = gpd.sjoin(points_gdf, gdf_map, how="inner", predicate="within")
                key_col = _pick_admin_key_column(joined.columns)
                if key_col is not None:
                    dist = {str(key): int(count) for key, count in joined[key_col].value_counts().items()}

    features = []
    for feature in admin_geojson.get("features", []):
        props = dict(feature.get("properties", {}))
        feature_level = str(props.get("level", "")).strip().lower()
        if feature_level != normalized_level:
            continue
        geometry = _simplify_feature_geometry(feature.get("geometry"), normalized_level)
        admin_key = _get_admin_key(props)
        display_name = props.get("name") or props.get("NAME") or props.get("fullname") or admin_key
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    **props,
                    "count": dist.get(admin_key, dist.get(str(display_name), 0)),
                    "name": display_name,
                },
            }
        )

    if special_region_features:
        features.extend(special_region_features)

    return {"geojson": {"type": "FeatureCollection", "features": features}}


def get_buffer_data(
    species: str,
    db: Session,
    radius_meters: float = 1000,
    year_from: int | None = None,
    year_to: int | None = None,
    include_unknown: bool = True,
) -> dict:
    locations = list_locations_by_species(db, species, None, year_from, year_to, include_unknown)
    if not locations:
        return {"geojson": {"type": "FeatureCollection", "features": []}}

    df = pd.DataFrame(locations)
    if df.empty or "longitude" not in df.columns or "latitude" not in df.columns:
        return {"geojson": {"type": "FeatureCollection", "features": []}}

    valid_df = df[(df["longitude"].notna()) & (df["latitude"].notna())].copy()
    if valid_df.empty:
        return {"geojson": {"type": "FeatureCollection", "features": []}}

    geometry = [Point(xy) for xy in zip(valid_df["longitude"], valid_df["latitude"])]
    points_gdf = gpd.GeoDataFrame(valid_df, geometry=geometry, crs="EPSG:4326")
    projected = points_gdf.to_crs(epsg=3857)
    buffers = projected.geometry.buffer(radius_meters)
    merged = unary_union(buffers.values)
    if merged.is_empty:
        return {"geojson": {"type": "FeatureCollection", "features": []}}

    buffer_gdf = gpd.GeoDataFrame(
        [{"radius_meters": radius_meters, "count": len(valid_df)}],
        geometry=[merged],
        crs="EPSG:3857",
    ).to_crs(epsg=4326)
    geojson = json.loads(buffer_gdf.to_json())
    return {"geojson": geojson}


def _normalize_admin_level(level: str) -> str:
    normalized = (level or "province").strip().lower()
    return {
        "省级": "province",
        "市级": "city",
        "区县级": "district",
    }.get(normalized, normalized or "province")


def _get_admin_key(props: dict) -> str:
    adcode = props.get("id") or props.get("ID") or props.get("adcode") or props.get("ADCODE")
    if adcode is not None:
        return str(adcode)
    name = props.get("name") or props.get("NAME") or props.get("fullname")
    return str(name or "")


def _pick_admin_key_column(columns) -> str | None:
    for candidate in ("id", "ID", "adcode", "ADCODE", "code", "CODE", "name", "NAME"):
        if candidate in columns:
            return candidate
    return None


def _build_special_region_fallback_features(
    province_geojson: dict | None,
    province_counts: dict[str, int],
    normalized_level: str,
) -> list[dict]:
    if normalized_level not in {"city", "district"}:
        return []
    if not province_geojson:
        return []

    special_names = {
        "710000": "台湾省",
        "810000": "香港特别行政区",
        "820000": "澳门特别行政区",
    }

    features: list[dict] = []
    for feature in province_geojson.get("features", []):
        props = dict(feature.get("properties", {}))
        adcode = str(props.get("adcode") or props.get("id") or "")
        name = str(props.get("name") or props.get("NAME") or "")
        if adcode not in special_names and name not in special_names.values():
            continue

        display_name = name or special_names.get(adcode, adcode)
        count = province_counts.get(display_name, province_counts.get(display_name.replace("特别行政区", ""), 0))
        if count <= 0:
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": _simplify_feature_geometry(feature.get("geometry"), "province"),
                "properties": {
                    **props,
                    "count": count,
                    "name": f"{display_name}（省级降级显示）",
                    "display_level": "province_fallback",
                    "source_level": normalized_level,
                },
            }
        )

    return features


def _is_special_region_province(value: str | None) -> bool:
    normalized = str(value or "").strip()
    return normalized in {"台湾省", "香港特别行政区", "澳门特别行政区", "香港", "澳门", "台湾", "臺灣省"}


@lru_cache(maxsize=8)
def _load_admin_geojson(level: str) -> dict | None:
    if level == "province":
        return get_china_geojson()

    csv_geojson = _load_areacity_csv_geojson(level)
    if csv_geojson is not None:
        return csv_geojson

    geo_root = get_settings().data_dir
    search_roots = [geo_root / "AreaCity_ok_geo", geo_root / "geo"]
    candidates = []
    for root in search_roots:
        if root.exists():
            candidates.extend(root.rglob("*.json"))

    candidates = sorted(
        candidates,
        key=lambda path: _score_admin_geojson_candidate(path, level),
        reverse=True,
    )

    for path in candidates:
        payload = _read_json_file(path)
        if not payload or payload.get("type") != "FeatureCollection":
            continue
        features = payload.get("features", [])
        if not features:
            continue

        matched_features = [
            feature
            for feature in features
            if str(feature.get("properties", {}).get("level", "")).strip().lower() == level
        ]
        if matched_features:
            return {"type": "FeatureCollection", "features": matched_features}

        if level in str(path).lower():
            return payload

    return None


def _load_areacity_csv_geojson(level: str) -> dict | None:
    csv_path = get_settings().data_dir / "AreaCity_ok_geo" / "ok_geo.csv"
    if not csv_path.is_file():
        return None

    target_deep = _admin_level_to_deep(level)
    if target_deep is None:
        return None

    records: list[dict] = []
    try:
        reader = pd.read_csv(
            csv_path,
            encoding="utf-8-sig",
            usecols=["id", "pid", "deep", "name", "ext_path", "geo", "polygon"],
            chunksize=5000,
            dtype={"id": "string", "pid": "string", "deep": "Int64", "name": "string", "ext_path": "string", "geo": "string", "polygon": "string"},
        )
    except Exception:
        return None

    for chunk in reader:
        filtered = chunk[chunk["deep"] == target_deep].copy()
        if filtered.empty:
            continue

        for row in filtered.itertuples(index=False):
            geometry = _parse_areacity_polygon(getattr(row, "polygon", None))
            if geometry is None or geometry.is_empty:
                continue

            level_name = _deep_to_level_name(int(getattr(row, "deep", target_deep)))
            records.append(
                {
                    "type": "Feature",
                    "geometry": mapping(geometry),
                    "properties": {
                        "id": str(getattr(row, "id", "") or ""),
                        "pid": str(getattr(row, "pid", "") or ""),
                        "deep": int(getattr(row, "deep", target_deep)),
                        "level": level_name,
                        "name": str(getattr(row, "name", "") or ""),
                        "ext_path": str(getattr(row, "ext_path", "") or ""),
                        "geo": str(getattr(row, "geo", "") or ""),
                    },
                }
            )

    if not records:
        return None

    return {"type": "FeatureCollection", "features": records}


def _admin_level_to_deep(level: str) -> int | None:
    normalized = _normalize_admin_level(level)
    return {
        "province": 0,
        "city": 1,
        "district": 2,
    }.get(normalized)


def _deep_to_level_name(deep: int) -> str:
    return {
        0: "province",
        1: "city",
        2: "district",
    }.get(deep, "province")


def _admin_simplify_tolerance(level: str) -> float:
    return {
        "province": 0.0,
        "city": 0.001,
        "district": 0.002,
    }.get(level, 0.0)


def _simplify_feature_geometry(geometry: dict | None, level: str) -> dict | None:
    if not geometry:
        return geometry

    tolerance = _admin_simplify_tolerance(level)
    if tolerance <= 0:
        return geometry

    try:
        simplified = shape(geometry).simplify(tolerance, preserve_topology=False)
        if simplified.is_empty:
            return geometry
        if not simplified.is_valid:
            return geometry
        return mapping(simplified)
    except Exception:
        return geometry


def _parse_areacity_polygon(polygon_text: str | None):
    if polygon_text is None or pd.isna(polygon_text):
        return None

    raw = str(polygon_text).strip()
    if not raw:
        return None

    parts = [part.strip() for part in re.split(r"\s*[;|]\s*", raw) if part.strip()]
    if not parts:
        parts = [raw]

    polygons = []
    for part in parts:
        coordinates = []
        for token in part.split(","):
            token = token.strip()
            if not token:
                continue
            pieces = token.split()
            if len(pieces) < 2:
                continue
            try:
                longitude = float(pieces[0])
                latitude = float(pieces[1])
            except ValueError:
                continue
            coordinates.append((longitude, latitude))

        if len(coordinates) < 3:
            continue
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])

        polygon = Polygon(coordinates)
        if polygon.is_empty:
            continue
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        if polygon.is_empty:
            continue
        polygons.append(polygon)

    if not polygons:
        return None
    if len(polygons) == 1:
        return polygons[0]
    return MultiPolygon(polygons)


def _score_admin_geojson_candidate(path: Path, level: str) -> int:
    lower = str(path).lower()
    score = 0
    if level in lower:
        score += 10
    if "areacity_ok_geo" in lower:
        score += 8
    if "geo" in lower:
        score += 1
    return score


def _read_json_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None





def _resolve_path_under_data_subdir(subdir: str, species: str, ext: str) -> Path | None:
    if not species or not str(species).strip():
        return None

    normalized = str(species).strip()
    if any(char in normalized for char in ("/", "\\", "\x00")) or ".." in normalized or ":" in normalized:
        return None

    base = (get_settings().data_dir / subdir).resolve()
    candidate = (base / f"{normalized}{ext}").resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate
