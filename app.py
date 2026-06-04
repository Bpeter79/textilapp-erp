import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from decimal import Decimal, ROUND_HALF_UP
import datetime

# --- KONFIGURÁCIÓ ---
# Használd a Supabase Connection String-et a Streamlit Secrets-ből
# Példa: postgresql://postgres:[JELSZÓ]@db.[PROJECT_ID].supabase.co:5432/postgres
@st.cache_resource
def get_engine():
    db_url = st.secrets["DATABASE_URL"]
    return create_engine(db_url)

engine = get_engine()

st.set_page_config(page_title="TextilApp ERP", page_icon="🧵", layout="wide")

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

# --- NAVIGÁCIÓ ---
menu = st.sidebar.radio("Modul", ["📊 Vezérlőpult", "🏢 Ügyfelek", "🚀 Projektek", "💰 Árajánlatok", "🖨️ Elszámolás"])

# --- VEZÉRLŐPULT ---
if menu == "📊 Vezérlőpult":
    st.title("📊 Vezérlőpult")
    try:
        u_szam = db_query("SELECT COUNT(*) FROM ugyfelek").iloc[0,0]
        st.metric("Ügyfelek száma", u_szam)
    except:
        st.error("Ellenőrizd, hogy a táblák létre lettek-e hozva a Supabase-ben!")

# --- ÜGYFELEK ---
elif menu == "🏢 Ügyfelek":
    st.title("🏢 Ügyfelek")
    with st.form("uj_ugyfel"):
        cegnev = st.text_input("Cégnév *")
        if st.form_submit_button("Mentés"):
            if db_exec("INSERT INTO ugyfelek (cegnev) VALUES (:c)", {"c": cegnev}):
                st.success("Sikeresen elmentve a Supabase-be!")
                st.rerun()
    
    st.dataframe(db_query("SELECT * FROM ugyfelek"))

# --- PROJEKTEK (Relációs) ---
elif menu == "🚀 Projektek":
    st.title("🚀 Projektek")
    ugyfelek = db_query("SELECT id, cegnev FROM ugyfelek")
    
    with st.form("uj_projekt"):
        p_nev = st.text_input("Projekt neve")
        u_valasztas = st.selectbox("Ügyfél", ugyfelek['cegnev'])
        u_id = ugyfelek[ugyfelek['cegnev'] == u_valasztas]['id'].iloc[0]
        
        if st.form_submit_button("Projekt indítása"):
            db_exec("INSERT INTO projektek (projekt_neve, ugyfel_id) VALUES (:n, :u)", 
                    {"n": p_nev, "u": int(u_id)})
            st.rerun()

    # JOIN lekérdezés megjelenítése
    st.subheader("Aktív projektek")
    q = "SELECT p.projekt_neve, u.cegnev FROM projektek p JOIN ugyfelek u ON p.ugyfel_id = u.id"
    st.dataframe(db_query(q))

# --- ELSZÁMOLÁS ---
elif menu == "🖨️ Elszámolás":
    st.title("🖨️ Elszámolás")
    st.info("Ez a modul az SQL tábláidból dolgozik.")
