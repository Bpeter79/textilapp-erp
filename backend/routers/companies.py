from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.config import supabase

router = APIRouter()

class ContactSchema(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None

class Company(BaseModel):
    id: Optional[str] = None
    company_name: str
    brand_name: Optional[str] = None
    tax_number: Optional[str] = None
    eu_tax_number: Optional[str] = None
    industry: Optional[str] = "Textilipar"
    status: Optional[str] = "active"
    company_type: Optional[str] = "business"
    role_type: Optional[str] = "customer"
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    payment_terms: Optional[str] = "8"
    currency: Optional[str] = "HUF"
    internal_notes: Optional[str] = None
    contacts: Optional[List[ContactSchema]] = []

@router.get("/companies")
def get_companies():
    # 'descending=True' helyett 'desc=True'-t kell írni!
    res = supabase.table("companies").select("*, contacts(*)").order("created_at", desc=True).execute()
    return res.data

@router.post("/companies")
def create_company(company: Company):
    try:
        company_data = company.model_dump()
        contacts_to_add = company_data.pop("contacts", [])
        company_data.pop("id", None)
        
        res = supabase.table("companies").insert(company_data).execute()
        created_company = res.data[0]
        
        for contact in contacts_to_add:
            contact.pop("id", None)
            contact["company_id"] = created_company["id"]
            supabase.table("contacts").insert(contact).execute()
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/companies/{company_id}")
def update_company(company_id: str, company: Company):
    try:
        company_data = company.model_dump()
        contacts_data = company_data.pop("contacts", [])
        company_data.pop("id", None)
        
        supabase.table("companies").update(company_data).eq("id", company_id).execute()
        
        supabase.table("contacts").delete().eq("company_id", company_id).execute()
        for contact in contacts_data:
            contact.pop("id", None)
            contact["company_id"] = company_id
            supabase.table("contacts").insert(contact).execute()
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/companies/{company_id}")
def delete_company(company_id: str):
    try:
        supabase.table("companies").delete().eq("id", company_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))