from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from graph_chain import get_chain, invoke_qa, invalidate_chain
from geo_data import (
    get_china_geojson,
    get_china_gdf,
    point_in_china,
    invalidate_geo_cache,
    geo_source,
    load_china_geojson,
)
from species_data import load_csv_for_gbif_file, clear_csv_cache
from qa_cache import qa_cache
from config import get_settings
from database import (
    init_db,
    get_db,
    get_species_list,
    get_locations_by_species,
    add_location_record,
    get_all_records,
    get_db_stats,
)
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import csv
import os
import requests
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from typing import Optional
import time
from sqlalchemy.orm import Session

# 模型定义
class QuestionRequest(BaseModel):
    question: str

class LocationRecord(BaseModel):
    species: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: str
    date: Optional[str] = None

app = FastAPI(title="水生入侵物种分析 API")


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": exc.errors()}},
    )


# 【关键配置】解决跨域问题（CORS）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _locations_record_file() -> str:
    """获取用户上报记录的CSV文件路径"""
    return str(get_settings().data_dir / "locations_record.csv")


def _resolved_path_under_data_subdir(subdir: str, species: str, ext: str) -> Optional[Path]:
    """
    将物种名解析为 data/<subdir> 下的安全路径，防止目录穿越攻击

    Args:
        subdir: 子目录名（如 'gbif_results', 'maxent_results'）
        species: 物种标识符
        ext: 文件扩展名（如 '.csv', '.tif'）

    Returns:
        安全的文件路径，或 None 如果输入非法
    """
    if not species or not str(species).strip():
        return None

    s = str(species).strip()

    # 检查危险字符
    if any(c in s for c in ("/", "\\", "\x00")):
        return None
    if ".." in s or ":" in s:  # 防止路径穿越
        return None

    root = get_settings().data_dir.resolve()
    base = (root / subdir).resolve()
    candidate = (base / f"{s}{ext}").resolve()

    # 验证解析后的路径仍然在 base 目录下
    try:
        candidate.relative_to(base)
    except ValueError:
        return None

    return candidate


# 静态目录，供 MaxEnt 预测PNG等文件访问
app.mount("/static", StaticFiles(directory=str(get_settings().data_dir)), name="static")


@app.on_event("startup")
async def _startup_load_geo():
    """优先加载省界（本地或联网并落盘），避免首请求才拉取；初始化数据库"""
    load_china_geojson(force_reload=False)
    # 初始化数据库
    init_db()


@app.get("/")
def read_root():
    return {"message": "后端服务已启动！可以开始查询水生外来入侵物种了！"}

# ========== 物种相关 API ==========
def _list_gbif_species_basenames(db: Session = None):
    """
    从数据库获取所有物种名称列表

    Returns:
        物种名称列表（按字母排序）
    """
    if db is None:
        from database import SessionLocal
        db = SessionLocal()
        try:
            return get_species_list(db)
        finally:
            db.close()
    return get_species_list(db)


def _resolve_species_for_graph_qa(raw: str, db: Session = None):
    """
    规范物种名称，与数据库中的名称对齐
    用于知识图谱查询时的物种匹配

    Args:
        raw: 用户输入的物种名（可能有大小写混淆）
        db: 数据库会话

    Returns:
        (规范名或原串, 是否在平台列表中)
    """
    s = (raw or "").strip()
    if not s:
        return "", False

    if db is None:
        from database import SessionLocal
        db = SessionLocal()
        try:
            names = get_species_list(db)
        finally:
            db.close()
    else:
        names = get_species_list(db)

    # 精确匹配
    if s in names:
        return s, True

    # 不区分大小写的匹配
    by_lower = {n.lower(): n for n in names}
    if s.lower() in by_lower:
        return by_lower[s.lower()], True

    return s, False


@app.get("/api/species")
def get_species_list():
    """获取所有物种列表"""
    try:
        return {"species": _list_gbif_species_basenames()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/species/{species}")
def get_species_info(species: str):
    """获取物种详细信息"""
    canonical, known = _resolve_species_for_graph_qa(species)
    display = canonical or species.strip()
    if known:
        cy_esc = canonical.replace("\\", "\\\\").replace("'", "\\'")
        graph_hint = (
            f"【图谱检索提示】本平台该物种标准名为「{canonical}」。"
            f"生成 Cypher 查询 Species 时，请对 s.name 使用模糊匹配"
            f"（例如 toLower(s.name) CONTAINS toLower('{cy_esc}')），不要假设图中名称与平台完全一致。\n"
        )
    else:
        graph_hint = (
            f"【图谱检索提示】用户输入为「{species.strip()}」；图中 Species.name 可能与平台 CSV 文件名不同，"
            "请用 CONTAINS、toLower 等做模糊匹配并尝试常见别名。\n"
        )
    question = (
        graph_hint
        + f"请介绍「{display}」的基本信息、危害与防治方法。若图谱查询无结果请在回答中说明。"
    )
    try:
        chain = get_chain()
        response = chain.invoke({"query": question})
        return {
            "info": response["result"],
            "cypher": response.get("generated_cypher", ""),
            "canonical_species": canonical if known else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"get_species_info: {e}")
        raise HTTPException(status_code=503, detail="暂无知识库数据或图谱不可用")

# ========== 地理位置相关 API ==========
def _get_locations_list(species: str, db: Session) -> list:
    """
    从数据库读取物种分布位置数据

    Args:
        species: 物种名称
        db: 数据库会话

    Returns:
        位置列表，每项包含: {"latitude", "longitude", "location_name"}

    Raises:
        HTTPException: 物种不存在时返回 400
    """
    locations = get_locations_by_species(db, species, limit=1000)

    if not locations:
        # 检查物种是否存在
        all_species = get_species_list(db)
        if species not in all_species:
            raise HTTPException(status_code=404, detail=f"物种 '{species}' 未找到")

    return locations


@app.get("/api/locations/{species}")
def get_locations(species: str, db: Session = Depends(get_db)):
    """获取物种分布位置（从数据库检索）"""
    try:
        locations = get_locations_by_species(db, species, limit=1000)
        return {"locations": locations}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get locations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== 图层与空间分析 API ==========

@app.get("/api/heatmap/{species}")
def get_heatmap(species: str, db: Session = Depends(get_db)):
    try:
        all_locs = get_locations_by_species(db, species)
    except HTTPException:
        raise
    points = []
    for loc in all_locs:
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        if lat is not None and lon is not None:
            points.append([lat, lon, 1.0])
    return {"points": points}


@app.get("/api/province-data/{species}")
def get_province_data(species: str, db: Session = Depends(get_db)):
    china_geojson = get_china_geojson()
    if not china_geojson:
        raise HTTPException(status_code=500, detail="中国省界 GeoJSON 尚未加载（请配置 data/geo/china_100000_full.json 或检查网络）")

    try:
        locations = get_locations_by_species(db, species)
    except HTTPException:
        raise

    # ==== 核心：基于经纬度的空间位置精确判定 ====
    dist = {}
    gdf_map = get_china_gdf()

    if gdf_map is not None and locations:
        df = pd.DataFrame(locations)
        # 确保有坐标才能运算
        if not df.empty and 'longitude' in df.columns and 'latitude' in df.columns:
            geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
            points_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

            # 空间连接：判断点落入哪个省份多边形
            joined = gpd.sjoin(points_gdf, gdf_map, how="inner", predicate='within')

            # 统计各省份出现的频次
            name_col = 'name' if 'name' in joined.columns else 'NAME'
            if name_col in joined.columns:
                dist = joined[name_col].value_counts().to_dict()

    # ==== 组装包含统计结果的 GeoJSON ====
    features = []
    for feat in china_geojson.get("features", []):
        props = dict(feat.get("properties", {}))
        province_name = props.get("name") or props.get("NAME") or props.get("fullname")
        # 直接使用空间统计的结果
        count = dist.get(province_name, 0)

        new_feat = {
            "type": "Feature",
            "geometry": feat.get("geometry"),
            "properties": {
                **props,
                "count": count,
                "name": province_name
            }
        }
        features.append(new_feat)

    return {"geojson": {"type": "FeatureCollection", "features": features}}

@app.get("/api/maxent-image/{species}")
def get_maxent_image(species: str):
    tif_path = _resolved_path_under_data_subdir("maxent_results", species, ".tif")
    if tif_path is None:
        return {"error": "无效的物种标识", "imageUrl": "", "bounds": []}
    png_path = tif_path.with_suffix(".png")
    if not tif_path.is_file():
        return {"error": "未找到 MaxEnt 结果文件", "imageUrl": "", "bounds": []}
    try:
        with rasterio.open(tif_path) as src:
            bounds = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]
            arr = src.read(1, masked=True).astype(np.float32)
            arr = np.ma.filled(arr, np.nan)
            vmin = np.nanmin(arr)
            vmax = np.nanmax(arr)
            if not (np.isfinite(vmin) and np.isfinite(vmax)) or vmin == vmax:
                norm = np.zeros_like(arr)
            else:
                norm = (arr - vmin) / (vmax - vmin)
            cmap = plt.get_cmap("YlOrRd")
            rgba = cmap(norm)
            rgba[..., 3] = np.where(np.isnan(arr), 0, 0.65)
            png_path.parent.mkdir(parents=True, exist_ok=True)
            plt.imsave(png_path, rgba)
        return {
            "imageUrl": f"/static/maxent_results/{tif_path.stem}.png",
            "bounds": bounds
        }
    except Exception as e:
        print(f"生成MaxEnt图像失败: {e}")
        return {"error": str(e), "imageUrl": "", "bounds": []}

@app.get("/api/geocode")
def geocode(address: str):
    try:
        time.sleep(1)  # 【安全保护】强制休眠 1 秒，严格遵守 OSM API 并发限制政策
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1}
        r = requests.get(url, params=params, headers={"User-Agent": "aquatic-species-platform"}, timeout=15)
        r.raise_for_status()
        arr = r.json()
        if not arr:
            raise HTTPException(status_code=404, detail="无法找到地址")
        first = arr[0]
        return {
            "lat": float(first["lat"]),
            "lon": float(first["lon"]),
            "display_name": first.get("display_name", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地理编码失败: {e}")

@app.get("/api/reverse-geocode")
def reverse_geocode(lat: float, lon: float):
    try:
        time.sleep(1)  # 【安全保护】强制休眠 1 秒，严格遵守 OSM API 并发限制政策
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json"}
        r = requests.get(url, params=params, headers={"User-Agent": "aquatic-species-platform"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        return {"address": data.get("display_name", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"逆向地理编码失败: {e}")

# ========== 知识问答 API ==========

@app.post("/api/qa")
def qa_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    知识图谱问答接口

    支持两种模式：
    1. 知识开接：直接从 Neo4j 知识图谱查询
    2. 降级模式：如果图谱不可用，自动使用 LLM 离线回答

    性能优化：支持 TTL 缓存，相同问题不重复计算
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    q = request.question.strip()
    names = get_species_list(db)

    # 检查缓存
    cached = qa_cache.get(q)
    if cached:
        return cached

    try:
        response = invoke_qa(q, names)
        out = {
            "answer": response.get("result", "无法获取回答"),
            "cypher": response.get("generated_cypher", ""),
            "from_template": bool(response.get("from_template", False)),
        }
        qa_cache.set(q, out)
        return out

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"QA Error: {e}")
        raise HTTPException(status_code=503, detail=f"暂时无法回答: {type(e).__name__}")


@app.get("/api/qa/suggestions/{species}")
def get_qa_suggestions(species: str):
    """获取针对某个物种的预设建议问题"""
    suggestions = [
        f"介绍一下 {species}",
        f"{species} 的危害是什么？",
        f"如何防治 {species}？",
        f"{species} 属于什么分类？",
        f"{species} 的原产地在哪？"
    ]
    return {"suggestions": suggestions}

# ========== 数据上报 API ==========

@app.post("/api/record/location")
def record_location(record: LocationRecord, db: Session = Depends(get_db)):
    """
    上报新的物种分布位置

    验证：
    - 坐标必须在中国境内（使用省界 GeoJSON）
    - 坐标范围应在合法范围内
    - 自动记录时间戳

    Returns:
        {"status": "success", "message": "记录已保存"}
    """
    # 先验证坐标在中国范围内
    inside = point_in_china(record.longitude, record.latitude)
    if inside is None:
        raise HTTPException(
            status_code=503,
            detail="国界参考数据未就绪。请将省界 GeoJSON 放入 data/geo/ 或检查网络后重试。",
        )
    if not inside:
        raise HTTPException(
            status_code=400,
            detail="坐标须位于中国境内（与省级地图使用的省界范围一致）。",
        )

    try:
        add_location_record(
            db,
            record.species,
            record.latitude,
            record.longitude,
            record.location_name,
            record.date,
        )
        return {"status": "success", "message": "记录已保存"}

    except Exception as e:
        print(f"Record Error: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {e}")


@app.get("/api/records")
def get_records(db: Session = Depends(get_db)):
    """获取所有用户上报的记录"""
    try:
        records = get_all_records(db)
        return {"records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _require_admin(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    s = get_settings()
    if not s.admin_api_key:
        raise HTTPException(status_code=503, detail="管理接口未配置 ADMIN_API_KEY")
    if x_admin_key != s.admin_api_key:
        raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/api/admin/cache/invalidate")
def admin_invalidate_cache(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """清空省界内存缓存、CSV 缓存、图谱链、问答缓存；需 X-Admin-Key。"""
    _require_admin(x_admin_key)
    invalidate_geo_cache()
    clear_csv_cache()
    invalidate_chain()
    qa_cache.clear()
    load_china_geojson(force_reload=True)
    return {"ok": True, "message": "已失效缓存并尝试重新加载省界数据"}


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """健康检查，包括数据库状态"""
    gj = get_china_geojson()
    from graph_chain import get_neo4j_graph

    neo = get_neo4j_graph()

    try:
        stats = get_db_stats(db)
    except Exception as e:
        stats = {"error": str(e)}

    return {
        "status": "ok",
        "china_geojson": bool(gj),
        "china_geo_source": geo_source(),
        "neo4j_connected": neo is not None,
        "database": stats,
    }
