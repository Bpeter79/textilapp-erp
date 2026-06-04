import streamlit as st
from supabase import create_client

@st.cache_resource
def get_db_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_db_client()

# --- LEKÉRDEZÉSEK ---
def get_companies():
    return supabase.table("companies").select("*").order("company_name").execute().data

def get_contacts_by_company(company_id):
    return supabase.table("contacts").select("*").eq("company_id", company_id).execute().data

def get_projects_by_company(company_id):
    return supabase.table("projects").select("*").eq("company_id", company_id).order("deadline_date").execute().data

def get_patterns_by_company(company_id):
    return supabase.table("patterns").select("*").eq("company_id", company_id).execute().data

def get_quotes_by_company(company_id):
    return supabase.table("quotes").select("*").eq("company_id", company_id).execute().data

def get_settlements_by_company(company_id):
    return supabase.table("settlements").select("*").eq("company_id", company_id).order("settlement_number", desc=True).execute().data

def get_all_settlement_items():
    return supabase.table("settlement_items").select("*").execute().data

def get_settlement_items(settlement_id):
    return supabase.table("settlement_items").select("*").eq("settlement_id", settlement_id).order("created_at").execute().data

# --- BESZÚRÁSOK ---
def insert_company(data):
    return supabase.table("companies").insert(data).execute()

def insert_contact(data):
    return supabase.table("contacts").insert(data).execute()

def insert_project(data):
    return supabase.table("projects").insert(data).execute()

def insert_pattern(data):
    return supabase.table("patterns").insert(data).execute()

def insert_quote(data):
    return supabase.table("quotes").insert(data).execute()

def insert_settlement(data):
    return supabase.table("settlements").insert(data).execute()

def insert_settlement_item(data):
    return supabase.table("settlement_items").insert(data).execute()

# --- MÓDOSÍTÁSOK ÉS TÖRLÉSEK (ÚJ) ---
def update_settlement(settlement_id, data):
    return supabase.table("settlements").update(data).eq("id", settlement_id).execute()

def update_settlement_item(item_id, data):
    return supabase.table("settlement_items").update(data).eq("id", item_id).execute()

def delete_settlement(settlement_id):
    return supabase.table("settlements").delete().eq("id", settlement_id).execute()

def delete_settlement_item(item_id):
    return supabase.table("settlement_items").delete().eq("id", item_id).execute()
