from fastapi import APIRouter

from app.services.provider_registry import get_provider_info


router = APIRouter(tags=["providers"])


@router.get("/providers")
def provider_status() -> dict:
    info = get_provider_info()
    return {
        name: {"selected": provider.selected, "available": provider.available}
        for name, provider in info.items()
    }
