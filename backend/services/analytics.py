from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from fastapi import HTTPException
from shapely.geometry import Point
from sqlalchemy.orm import Session

from config import get_settings
from domain.geo_data import get_china_gdf, get_china_geojson
from repositories.species_repository import list_locations_by_species


def get_heatmap(species: str, db: Session) -> dict[str, list[list[float]]]:
    points: list[list[float]] = []
    for location in list_locations_by_species(db, species):
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is not None and lon is not None:
            points.append([lat, lon, 1.0])
    return {"points": points}


def get_province_data(species: str, db: Session) -> dict:
    china_geojson = get_china_geojson()
    if not china_geojson:
        raise HTTPException(status_code=500, detail="中国省界 GeoJSON 尚未加载。")

    locations = list_locations_by_species(db, species)
    dist: dict[str, int] = {}
    gdf_map = get_china_gdf()

    if gdf_map is not None and locations:
        df = pd.DataFrame(locations)
        if not df.empty and "longitude" in df.columns and "latitude" in df.columns:
            geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]
            points_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
            joined = gpd.sjoin(points_gdf, gdf_map, how="inner", predicate="within")
            name_col = "name" if "name" in joined.columns else "NAME"
            if name_col in joined.columns:
                dist = joined[name_col].value_counts().to_dict()

    features = []
    for feature in china_geojson.get("features", []):
        props = dict(feature.get("properties", {}))
        province_name = props.get("name") or props.get("NAME") or props.get("fullname")
        features.append(
            {
                "type": "Feature",
                "geometry": feature.get("geometry"),
                "properties": {
                    **props,
                    "count": dist.get(province_name, 0),
                    "name": province_name,
                },
            }
        )

    return {"geojson": {"type": "FeatureCollection", "features": features}}





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
