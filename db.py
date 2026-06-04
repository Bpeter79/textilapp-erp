from supabase import create_client
import streamlit as st

@st.cache_resource
def get_db_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_db_client()

def get_all_companies():
    return supabase.table("companies").select("*").execute().data

def insert_company(name, tax, addr):
    return supabase.table("companies").insert({"name": name, "tax_number": tax, "address": addr}).execute()

def insert_project(company_id, name, status, deadline):
    return supabase.table("projects").insert({
        "company_id": company_id, "project_name": name, "status": status, "deadline": deadline
    }).execute()
