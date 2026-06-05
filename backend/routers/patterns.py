from fastapi import APIRouter, HTTPException, status
from typing import List
from core.config import supabase
from schemas import schemas

router = APIRouter(prefix="/patterns", tags=["Patterns - Szabásminták és Modellek"])

@router.post("", response_model=schemas.PatternOut, status_code=status.HTTP_201_CREATED)
def create_pattern(pattern: schemas.PatternCreate):
    """Új modellezési alaplap vagy szabásminta regisztrálása"""
    res = supabase.table("patterns").insert(pattern.model_dump()).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Nem sikerült menteni a szabásmintát.")
    return res.data[0]

@router.get("", response_model=List[schemas.PatternOut])
def list_patterns():
    """Összes szabásminta kilistázása"""
    res = supabase.table("patterns").select("*").order("item_number").execute()
    return res.data