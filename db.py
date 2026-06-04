import streamlit as st
from supabase import create_client

# Adatbázis kapcsolat inicializálása
@st.cache_resource
def get_db_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_db_client()

# --- CÉGEK (Companies) ---
def get_all_companies():
    return supabase.table("companies").select("*").order("created_at", desc=True).execute().data

def insert_company(name, tax_number, address, extra_data=None):
    return supabase.table("companies").insert({
        "name": name,
        "tax_number": tax_number,
        "address": address,
        "extra_data": extra_data or {}
    }).execute()

# --- KAPCSOLATTARTÓK (Contacts) ---
def get_contacts_by_company(company_id):
    return supabase.table("contacts").select("*").eq("company_id", company_id).execute().data

def insert_contact(company_id, first_name, last_name, email, role):
    return supabase.table("contacts").insert({
        "company_id": company_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "role": role
    }).execute()

# --- PROJEKTEK (Projects) ---
def insert_project(company_id, project_name, status, deadline):
    return supabase.table("projects").insert({
        "company_id": company_id,
        "project_name": project_name,
        "status": status,
        "deadline": deadline
    }).execute()
