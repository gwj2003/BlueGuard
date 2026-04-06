from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.errors import register_exception_handlers
from api.router import api_router
from config import get_settings
from database import init_db
from geo_data import load_china_geojson


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Aquatic Species Analysis API")

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=str(settings.data_dir)), name="static")
    app.include_router(api_router)

    @app.on_event("startup")
    async def _startup() -> None:
        settings.runtime_dir.mkdir(parents=True, exist_ok=True)
        load_china_geojson(force_reload=False)
        init_db()

    @app.get("/")
    def read_root():
        return {"message": "后端服务已启动，可以开始查询水生外来入侵物种了。"}

    return app


app = create_app()
