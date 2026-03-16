from fastapi import APIRouter, Depends

from ...core.config import Settings, get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/ping", summary="Health check")
def ping(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.api_title,
        "version": settings.api_version,
    }
