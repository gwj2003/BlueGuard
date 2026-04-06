from fastapi import APIRouter, Depends

from services.admin import invalidate_all_caches, require_admin


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/cache/invalidate")
def admin_invalidate_cache(_: None = Depends(require_admin)):
    return invalidate_all_caches()
