from fastapi import APIRouter

from api.routes.admin import router as admin_router
from api.routes.analytics import router as analytics_router
from api.routes.geo import router as geo_router
from api.routes.qa import router as qa_router
from api.routes.records import router as records_router
from api.routes.species import router as species_router
from api.routes.system import router as system_router


api_router = APIRouter()
api_router.include_router(species_router)
api_router.include_router(analytics_router)
api_router.include_router(geo_router)
api_router.include_router(qa_router)
api_router.include_router(records_router)
api_router.include_router(admin_router)
api_router.include_router(system_router)
