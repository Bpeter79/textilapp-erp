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

APP_VERSION = "5.1"

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
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=2
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
        st.error("Adatbázis hiba")
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

def get_list(table, field):
    df = db_query(f"SELECT DISTINCT {field} FROM {table} WHERE {field} IS NOT NULL ORDER BY {field}")
    return df[field].tolist() if not df.empty else []

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
    st.title("📊 Dashboard")

    c1, c2, c3 = st.columns(3)
    c1.metric("Ügyfelek", scalar("SELECT COUNT(*) FROM ugyfelek"))
    c2.metric("Projektek", scalar("SELECT COUNT(*) FROM projektek"))
    c3.metric("Elszámolások", scalar("SELECT COUNT(*) FROM elszamolasok"))

# ============================================================
# ÜGYFELEK (FIXED!)
# ============================================================

if menu == "🏢 Ügyfelek":

    st.title("🏢 Ügyfél Központ")

    keres = st.text_input("🔍 Keresés")

    params = {}
    q = "SELECT * FROM ugyfelek WHERE 1=1"

    if keres:
        q += " AND cegnev ILIKE :k"
        params["k"] = f"%{keres}%"

    df = db_query(q, params)

    if not df.empty:

        for _, row in df.iterrows():

            ceg = row["cegnev"]

            with st.container():
                st.markdown(f"### 🏢 {ceg}")

                col1, col2, col3 = st.columns(3)

                col1.write(f"📧 {row.get('email','-')}")
                col1.write(f"📞 {row.get('telefon','-')}")

                col2.write(f"🏭 {row.get('iparag','-')}")
                col2.write(f"💳 {row.get('fizetesi_feltetel','-')}")

                # ✅ FIXED SAFE SQL
                proj = scalar(
                    "SELECT COUNT(*) FROM projektek WHERE ugyfel_neve = :c",
                    {"c": ceg}
                )
                bev = scalar(
                    "SELECT COALESCE(SUM(brutto_ft),0) FROM elszamolasok WHERE ugyfel_neve = :c",
                    {"c": ceg}
                )
                ora = scalar(
                    "SELECT COALESCE(SUM(munkaora),0) FROM idokovetes WHERE ugyfel_neve = :c",
                    {"c": ceg}
                )

                col3.metric("📁 Projektek", proj)
                col3.metric("💰 Bevétel", f"{int(bev):,} Ft")
                col3.metric("⏱️ Óra", f"{float(ora):.1f}")

                st.markdown("---")

# ============================================================
# PROJEKTEK
# ============================================================

if menu == "🚀 Projektek":
    st.title("Projektek")

    ugyfel_lista = get_list("ugyfelek", "cegnev")

    with st.form("proj"):
        pszam = st.text_input("Projekt szám")
        pnev = st.text_input("Megnevezés")
        ugyfel = st.selectbox("Ügyfél", ugyfel_lista)

        if st.form_submit_button("Mentés"):
            db_exec("""
                INSERT INTO projektek (projekt_szam, projekt_neve, ugyfel_neve)
                VALUES (:s,:n,:u)
            """, {"s": pszam, "n": pnev, "u": ugyfel})

            st.success("Mentve")

    st.dataframe(db_query("SELECT * FROM projektek"))

# ============================================================
# ELSZÁMOLÁS
# ============================================================

if menu == "🖨️ Elszámolás":
    st.title("Elszámolás")

    ugyfel_lista = get_list("ugyfelek", "cegnev")

    with st.form("elsz"):
        kod = st.text_input("Kód")
        ugyfel = st.selectbox("Ügyfél", ugyfel_lista)
        netto = st.number_input("Nettó", 0)

        if st.form_submit_button("Mentés"):
            brutto = netto_to_brutto(netto)

            db_exec("""
                INSERT INTO elszamolasok (elsz_szam, ugyfel_neve, netto_ft, brutto_ft)
                VALUES (:k,:u,:n,:b)
            """, {
                "k": kod,
                "u": ugyfel,
                "n": netto,
                "b": brutto
            })

            st.success("Mentve")

    st.dataframe(db_query("SELECT * FROM elszamolasok"))

# ============================================================
# IDŐ
# ============================================================

if menu == "📱 Időkövetés":
    st.title("Időkövetés")

    projektek = get_list("projektek", "projekt_szam")

    with st.form("ido"):
        p = st.selectbox("Projekt", projektek)
        ora = st.number_input("Óra", 1.0)
        tev = st.text_input("Tevékenység")

        if st.form_submit_button("Mentés"):
            db_exec("""
                INSERT INTO idokovetes (projekt_szam, datum, tevekenyseg, munkaora)
                VALUES (:p,:d,:t,:m)
            """, {
                "p": p,
                "d": str(datetime.date.today()),
                "t": sanitize(tev),
                "m": ora
            })

            st.success("Mentve")

    df = db_query("SELECT * FROM idokovetes")

    if not df.empty:
        st.metric("Összes óra", f"{df['munkaora'].sum():.1f}")
        st.dataframe(df)
