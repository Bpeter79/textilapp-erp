"""
TextilApp ERP v4.2 — Supabase (PostgreSQL) verzió
"""
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- ADATBÁZIS KAPCSOLAT ---
@st.cache_resource
def get_engine():
    # A Streamlit Secrets-ben beállított DATABASE_URL használata
    return create_engine(st.secrets["DATABASE_URL"])

engine = get_engine()

# --- SEGÉDFÜGGVÉNYEK ---
def db_query(sql, params=None):
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})

def db_exec(sql, params=None):
    try:
        with engine.begin() as conn:
            conn.execute(text(sql), params or {})
        return True
    except Exception as e:
        st.error(f"Adatbázis hiba: {e}")
        return False

# --- UI BEÁLLÍTÁS ---
st.set_page_config(page_title="TextilApp ERP", layout="wide")
st.sidebar.title("🧵 TextilApp ERP v4.2")

# --- MENÜ ---
menu = st.sidebar.radio("Modul", [
    "📊 Vezérlőpult", "🏢 Ügyfelek", "🚀 Projektek", "✂️ Szabásminták", 
    "📦 Anyagjegyzék", "📐 Mérettáblák", "📝 Dokumentáció", "💰 Árajánlatok", 
    "🖨️ Elszámolás", "📱 Időkövetés"
])

# --- DINAMIKUS ADATKEZELÉS ---
# Példa: Ügyfél lekérdezés a 710 sorhoz igazítva
if menu == "🏢 Ügyfelek":
    st.title("🏢 Ügyfelek")
    # Keresés a 710 sorban
    keres = st.text_input("Keresés ügyfél név alapján")
    query = "SELECT * FROM ugyfelek"
    if keres:
        query += f" WHERE cegnev ILIKE '%{keres}%'"
    
    df = db_query(query)
    st.dataframe(df, use_container_width=True)

# --- FONTOS: Mivel a táblákat már létrehoztad (a korábbi SQL kódoddal), 
# a Python kód most már csak a már meglévő táblákba ír.
