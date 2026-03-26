from fastapi import APIRouter, Query

from app.schemas.symbols import SymbolProfile
from app.services.provider_registry import get_symbol_lookup_provider


router = APIRouter(tags=["symbols"])


@router.get("/symbols/profile", response_model=SymbolProfile)
def get_symbol_profile(symbol: str = Query(..., min_length=1)) -> SymbolProfile:
    return get_symbol_lookup_provider().get_profile(symbol)
