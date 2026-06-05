from fastapi import APIRouter, HTTPException, status
from typing import List
from core.config import supabase
from schemas import schemas

router = APIRouter(prefix="/settlements", tags=["Settlements - Elszámolási Jegyzékek"])

@router.post("", response_model=schemas.SettlementOut, status_code=status.HTTP_201_CREATED)
def create_settlement(settlement: schemas.SettlementCreate):
    """Új elszámolási jegyzék piszkozat létrehozása"""
    res = supabase.table("settlements").insert(settlement.model_dump()).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Nem sikerült létrehozni az elszámolást.")
    return res.data[0]

@router.get("/{settlement_id}", response_model=schemas.SettlementOut)
def get_settlement(settlement_id: str):
    """Egy konkrét elszámolási jegyzék lekérése a hozzá tartozó tételekkel együtt"""
    # 1. Elszámolás törzsadat lekérése
    sett_res = supabase.table("settlements").select("*").eq("id", settlement_id).execute()
    if not sett_res.data:
        raise HTTPException(status_code=404, detail="Az elszámolás nem található.")
    
    settlement_data = sett_res.data[0]
    
    # 2. A hozzá tartozó altételek lekérése (on-the-fly beágyazás)
    items_res = supabase.table("settlement_items").select("*").eq("settlement_id", settlement_id).execute()
    settlement_data["items"] = items_res.data if items_res.data else []
    
    return settlement_data