import re
import html
import datetime
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# ============================================================
# CONFIG
# ============================================================

APP_VERSION = "6.0"

DATABASE_URL = "postgresql://postgres.jrsjedpwcsrcbumonmtn:A6iz6u19790723@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"

st.set_page_config(page_title=f"TextilApp ERP v{APP_VERSION}", layout="wide")

# ============================================================
# ENGINE
# ============================================================

@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True
    )

engine = get_engine()

# ============================================================
# HELPERS
# ============================================================

def sanitize(val):
    if not isinstance(val, str):
        return str(val)
    val = re.sub(r'[\x00-\x1f\x7f]', '', val)
    return html.escape(val.strip())

def netto_to_brutto(netto, afa=27):
    n = Decimal(str(netto))
    return int((n * (Decimal('1') + Decimal(afa) / 100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def db_query(sql, params=None):
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    except Exception as e:
        st.error("DB hiba")
        st.exception(e)
        return pd.DataFrame()

def db_exec(sql, params=None):
    try:
        with engine.begin() as conn:
            conn.execute(text(sql), params or {})
        return True
    except Exception as e:
        st.error(str(e))
        return False

def scalar(sql, params=None):
    df = db_query(sql, params)
    return df.iloc[0, 0] if not df.empty else 0

# ============================================================
# NAV
# ============================================================

menu = st.sidebar.radio("Modul", [
    "📊 Dashboard",
    "🏢 Ügyfelek",
    "🚀 Projektek",
    "🖨️ Elszámolás",
    "📱 Időkövetés"
])

# ============================================================
# DASHBOARD
# ============================================================

if menu == "📊 Dashboard":
    st.title("Dashboard")

    st.metric("Ügyfelek", scalar("SELECT COUNT(*) FROM ugyfelek"))
    st.metric("Projektek", scalar("SELECT COUNT(*) FROM projektek"))

# ============================================================
# ÜGYFELEK ✅ FIXED
# ============================================================

if menu == "🏢 Ügyfelek":

    st.title("Ügyfelek")

    df = db_query("SELECT * FROM ugyfelek ORDER BY id DESC")

    if not df.empty:

        for _, row in df.iterrows():

            ceg = row["cegnev"]
            uid = row["id"]

            st.markdown(f"### 🏢 {ceg}")

            col1, col2, col3 = st.columns(3)

            col1.write(f"📧 {row.get('email','-')}")
            col1.write(f"📞 {row.get('telefon','-')}")

            # ✅ ID alapú kapcsolatok (EZ A FIX!)

            proj = scalar("""
                SELECT COUNT(*)
                FROM projektek
                WHERE ugyfel_id = :id
            """, {"id": uid})

            bev = scalar("""
                SELECT COALESCE(SUM(brutto_ft),0)
                FROM elszamolasok
                WHERE ugyfel_id = :id
            """, {"id": uid})

            ora = scalar("""
                SELECT COALESCE(SUM(munkaora),0)
                FROM idokovetes
                WHERE ugyfel_id = :id
            """, {"id": uid})

            col3.metric("📁 Projektek", proj)
            col3.metric("💰 Bevétel", f"{int(bev):,} Ft")
            col3.metric("⏱️ Óra", f"{float(ora):.1f}")

            st.markdown("---")

# ============================================================
# PROJEKTEK ✅ FIXED
# ============================================================

if menu == "🚀 Projektek":

    st.title("Projektek")

    ugyfelek = db_query("SELECT id, cegnev FROM ugyfelek")

    with st.form("proj"):
        pszam = st.text_input("Projekt szám")
        pnev = st.text_input("Név")

        ugyfel = st.selectbox(
            "Ügyfél",
            ugyfelek["cegnev"].tolist()
        )

        if st.form_submit_button("Mentés"):

            uid = int(ugyfelek[ugyfelek["cegnev"] == ugyfel]["id"].iloc[0])

            db_exec("""
                INSERT INTO projektek
                (projekt_szam, projekt_neve, ugyfel_id)
                VALUES (:s,:n,:u)
            """, {"s": pszam, "n": pnev, "u": uid})

            st.success("Mentve ✅")

# ============================================================
# ELSZÁMOLÁS ✅ FIXED
# ============================================================

if menu == "🖨️ Elszámolás":

    st.title("Elszámolás")

    ugyfelek = db_query("SELECT id, cegnev FROM ugyfelek")

    with st.form("elsz"):

        kod = st.text_input("Kód")
        ugyfel = st.selectbox("Ügyfél", ugyfelek["cegnev"])

        netto = st.number_input("Nettó", 0)

        if st.form_submit_button("Mentés"):

            uid = int(ugyfelek[ugyfelek["cegnev"] == ugyfel]["id"].iloc[0])
            brutto = netto_to_brutto(netto)

            db_exec("""
                INSERT INTO elszamolasok
                (elsz_szam, ugyfel_id, netto_ft, brutto_ft)
                VALUES (:k,:u,:n,:b)
            """, {
                "k": kod,
                "u": uid,
                "n": netto,
                "b": brutto
            })

            st.success("Mentve ✅")

# ============================================================
# IDŐKÖVETÉS ✅ FIXED
# ============================================================

if menu == "📱 Időkövetés":

    st.title("Időkövetés")

    projektek = db_query("SELECT id, projekt_szam FROM projektek")

    with st.form("ido"):

        p = st.selectbox("Projekt", projektek["projekt_szam"])

        ora = st.number_input("Óra", 1.0)
        tev = st.text_input("Tevékenység")

        if st.form_submit_button("Mentés"):

            pid = int(projektek[projektek["projekt_szam"] == p]["id"].iloc[0])

            db_exec("""
                INSERT INTO idokovetes
                (projekt_id, datum, tevekenyseg, munkaora)
                VALUES (:p,:d,:t,:m)
            """, {
                "p": pid,
                "d": str(datetime.date.today()),
                "t": tev,
                "m": ora
            })

            st.success("Mentve ✅")
