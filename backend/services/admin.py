from __future__ import annotations

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from config import get_settings
from geo_data import geo_source, get_china_geojson, invalidate_geo_cache, load_china_geojson
from graph_chain import get_neo4j_graph, invalidate_chain
from qa_cache import qa_cache
from repositories.stats_repository import get_db_stats
from species_data import clear_csv_cache


def require_admin(x_admin_key: str | None = Header(None, alias="X-Admin-Key")) -> None:
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="管理接口未配置 ADMIN_API_KEY")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Forbidden")


def invalidate_all_caches() -> dict[str, object]:
    invalidate_geo_cache()
    clear_csv_cache()
    invalidate_chain()
    qa_cache.clear()
    load_china_geojson(force_reload=True)
    return {"ok": True, "message": "缓存已失效并尝试重新加载省界数据"}


def get_health_status(db: Session) -> dict:
    try:
        stats = get_db_stats(db)
    except Exception as exc:
        stats = {"error": str(exc)}

    return {
        "status": "ok",
        "china_geojson": bool(get_china_geojson()),
        "china_geo_source": geo_source(),
        "neo4j_connected": get_neo4j_graph() is not None,
        "database": stats,
    }
