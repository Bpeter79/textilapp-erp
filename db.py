import streamlit as st
from supabase import create_client

@st.cache_resource
def get_db_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_db_client()

def get_all_companies():
    try:
        return supabase.table("companies").select("*").order("created_at", desc=True).execute().data
    except Exception as e:
        st.error(f"Adatbázis hiba: {e}")
        return []

def insert_company(name, tax_number, address, extra_data):
    return supabase.table("companies").insert({
        "name": name,
        "tax_number": tax_number,
        "address": address,
        "extra_data": extra_data
    }).execute()

def get_contacts_by_company(company_id):
    return supabase.table("contacts").select("*").eq("company_id", company_id).execute().data

def insert_contact(company_id, fn, ln, email, role):
    return supabase.table("contacts").insert({
        "company_id": company_id, "first_name": fn, "last_name": ln, "email": email, "role": role
    }).execute()
