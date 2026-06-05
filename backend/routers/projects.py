from fastapi import APIRouter, HTTPException, status
from typing import List
from core.config import supabase
from schemas import schemas

router = APIRouter(prefix="/projects", tags=["Projects - Projektek és Megrendelések"])

@router.post("", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate):
    """Új projekt / megrendelés indítása egy ügyfélhez"""
    res = supabase.table("projects").insert(project.model_dump()).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Nem sikerült létrehozni a projektet.")
    return res.data[0]

@router.get("", response_model=List[schemas.ProjectOut])
def list_projects():
    """Összes projekt listázása"""
    res = supabase.table("projects").select("*").order("created_at", descending=True).execute()
    return res.data

@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: str):
    """Egy konkrét projekt részletei ID alapján"""
    res = supabase.table("projects").select("*").eq("id", project_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="A projekt nem található.")
    return res.data[0]