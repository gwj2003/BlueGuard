import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.errors import register_exception_handlers
from api.router import api_router
from config import get_settings
from database import ensure_seed_data
import threading
import time

from domain.geo_data import preload_china_geo_cache
from services.analytics import preload_admin_geojson_cache


def _wildcard_origin_to_regex(origin: str) -> str:
    """Convert wildcard origins (e.g. https://*.ngrok.io) to anchored regex."""
    escaped = re.escape(origin)
    return f"^{escaped.replace(r'\\*', '.*')}$"


def create_app() -> FastAPI:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="Aquatic Species Analysis API")

    register_exception_handlers(app)

    # 处理 CORS 配置：支持正则表达式模式和通配符
    cors_kwargs = {
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    
    # 检查是否有正则表达式或通配符模式
    allow_origins_list = settings.allow_origins if isinstance(settings.allow_origins, list) else [settings.allow_origins]
    regex_patterns = [origin for origin in allow_origins_list if origin.startswith("https://*.")]
    simple_origins = [origin for origin in allow_origins_list if not origin.startswith("https://*.")]
    
    if regex_patterns:
        # 转换 https://*.ngrok.io 为正则表达式
        regex_pattern = "|".join(_wildcard_origin_to_regex(pattern) for pattern in regex_patterns)
        cors_kwargs["allow_origin_regex"] = regex_pattern
    
    if simple_origins:
        cors_kwargs["allow_origins"] = simple_origins
    
    app.add_middleware(CORSMiddleware, **cors_kwargs)

    app.mount("/static", StaticFiles(directory=str(settings.data_dir)), name="static")
    app.include_router(api_router)

    @app.on_event("startup")
    async def _startup() -> None:
        settings.runtime_dir.mkdir(parents=True, exist_ok=True)
        # 立即预热中国省界与衍生几何，减轻首次点查的开销
        preload_china_geo_cache()

        # 后台缓慢预热行政区 GeoJSON（province/city/district），避免在启动期间占满内存
        def _background_admin_preload():
            try:
                # 先短延迟，再分阶段加载，降低启动瞬时压力
                time.sleep(5)
                try:
                    preload_admin_geojson_cache(levels=("province",))
                except Exception as e:
                    print(f"后台预热省级行政区失败: {e}")

                # 稍后加载市级，再更晚加载区县级
                time.sleep(10)
                try:
                    preload_admin_geojson_cache(levels=("city",))
                except Exception as e:
                    print(f"后台预热市级行政区失败: {e}")

                time.sleep(20)
                try:
                    preload_admin_geojson_cache(levels=("district",))
                except Exception as e:
                    print(f"后台预热区县级行政区失败: {e}")
            except Exception as e:
                print(f"后台行政区分阶段预热出现异常: {e}")

        thread = threading.Thread(target=_background_admin_preload, daemon=True)
        thread.start()
        ensure_seed_data()

    @app.get("/")
    def read_root():
        return {"message": "后端服务已启动，可以开始查询水生外来入侵物种了。"}

    return app


app = create_app()
