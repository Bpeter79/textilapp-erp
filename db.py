
import streamlit as st
from supabase import create_client

# 1. Kapcsolat inicializálása
@st.cache_resource
def get_db_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_db_client()

# --- CÉGEK (Companies) ---
def get_companies():
    """Az összes cég lekérdezése."""
    return supabase.table("companies").select("*").execute().data

def insert_company(name, tax_number, address, extra_data=None):
    """Új cég rögzítése JSONB támogatással."""
    data = {
        "name": name,
        "tax_number": tax_number,
        "address": address,
        "extra_data": extra_data or {}
    }
    return supabase.table("companies").insert(data).execute()

# --- KAPCSOLATTARTÓK (Contacts) ---
def get_contacts(company_id=None):
    """Kapcsolattartók lekérdezése (opcionálisan cég szerint szűrve)."""
    query = supabase.table("contacts").select("*")
    if company_id:
        query = query.eq("company_id", company_id)
    return query.execute().data

def insert_contact(company_id, first_name, last_name, email, role):
    """Kapcsolattartó hozzáadása."""
    data = {
        "company_id": company_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "role": role
    }
    return supabase.table("contacts").insert(data).execute()

# --- PROJEKTEK (Projects) ---
def insert_project(company_id, project_name, status, deadline):
    """Projekt rögzítése."""
    data = {
        "company_id": company_id,
        "project_name": project_name,
        "status": status,
        "deadline": deadline
    }
    return supabase.table("projects").insert(data).execute()
