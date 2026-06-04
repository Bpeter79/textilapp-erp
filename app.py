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

APP_VERSION = "5.0"

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
    return int(
        (n * (Decimal('1') + Decimal(afa) / 100))
        .quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    )

def db_query(sql, params=None):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})

def db_exec(sql, params=None):
    try:
        with engine.begin() as conn:
            conn.execute(text(sql), params or {})
        return True
    except Exception as e:
        if "duplicate" in str(e).lower():
            st.error("❌ Már létezik!")
        else:
            st.error(str(e))
        return False

def get_list(table, field):
    df = db_query(f"SELECT DISTINCT {field} FROM {table} WHERE {field} IS NOT NULL ORDER BY {field}")
    return df[field].tolist() if not df.empty else []

# ============================================================
# NAVI
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

    def scalar(q):
        df = db_query(q)
        return int(df.iloc[0, 0]) if not df.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Ügyfelek", scalar("SELECT COUNT(*) FROM ugyfelek"))
    col2.metric("Projektek", scalar("SELECT COUNT(*) FROM projektek"))
    col3.metric("Elszámolás", scalar("SELECT COUNT(*) FROM elszamolasok"))

    df = db_query("SELECT kiallitas, netto_ft FROM elszamolasok ORDER BY kiallitas")
    if not df.empty:
        df["kiallitas"] = pd.to_datetime(df["kiallitas"])
        st.bar_chart(df.set_index("kiallitas"))

# ============================================================
# ÜGYFELEK
# ============================================================

if menu == "🏢 Ügyfelek":

    st.title("🏢 Ügyfelek")

    tab1, tab2 = st.tabs(["➕ Új ügyfél", "📋 Lista"])

    # ======================================================
    # ÚJ ÜGYFÉL
    # ======================================================
    with tab1:
        with st.form("ugyfel_form", clear_on_submit=True):

            col1, col2 = st.columns(2)

            cegnev = col1.text_input("Cégnév *")
            email = col2.text_input("Email")

            telefon = col1.text_input("Telefon")
            weboldal = col2.text_input("Weboldal")

            iparag = col1.text_input("Iparág")
            fizetes = col2.text_input("Fizetési feltétel")

            kedv = col1.number_input("Kedvezmény %", 0.0, 100.0, 0.0)

            megjegyzes = st.text_area("Megjegyzés")

            if st.form_submit_button("💾 Mentés"):

                if not cegnev:
                    st.error("Cégnév kötelező!")
                else:
                    ok = db_exec("""
                        INSERT INTO ugyfelek
                        (cegnev, email, telefon, weboldal,
                         iparag, fizetesi_feltetel, kedvezmeny_pct, megjegyzes)
                        VALUES
                        (:c,:e,:t,:w,:i,:f,:k,:m)
                    """, {
                        "c": sanitize(cegnev),
                        "e": sanitize(email),
                        "t": sanitize(telefon),
                        "w": sanitize(weboldal),
                        "i": sanitize(iparag),
                        "f": sanitize(fizetes),
                        "k": float(kedv),
                        "m": sanitize(megjegyzes)
                    })

                    if ok:
                        st.success("✅ Ügyfél mentve!")
                        st.rerun()

    # ======================================================
    # LISTA + KERESÉS


# ============================================================
# PROJEKTEK
# ============================================================

if menu == "🚀 Projektek":
    st.title("Projektek")

    ugyfel_lista = get_list("ugyfelek", "cegnev")

    with st.form("proj"):
        p_szam = st.text_input("Projekt szám *")
        p_nev = st.text_input("Név *")
        p_ugyfel = st.selectbox("Ügyfél", ugyfel_lista) if ugyfel_lista else ""

        if st.form_submit_button("Mentés"):
            if p_szam and p_nev:
                ok = db_exec("""
                    INSERT INTO projektek (projekt_szam, projekt_neve, ugyfel_neve)
                    VALUES (:s,:n,:u)
                """, {"s": p_szam, "n": sanitize(p_nev), "u": p_ugyfel})

                if ok:
                    st.success("Projekt mentve")
                    st.rerun()

    st.dataframe(db_query("SELECT * FROM projektek ORDER BY id DESC"))

# ============================================================
# ELSZÁMOLÁS
# ============================================================

if menu == "🖨️ Elszámolás":
    st.title("Elszámolás")

    ugyfel_lista = get_list("ugyfelek", "cegnev")

    with st.form("elsz"):
        kod = st.text_input("Elszámolás szám *")
        ugyfel = st.selectbox("Ügyfél", ugyfel_lista)
        netto = st.number_input("Nettó Ft", value=0)

        if st.form_submit_button("Mentés"):
            brutto = netto_to_brutto(netto)

            ok = db_exec("""
                INSERT INTO elszamolasok
                (elsz_szam, ugyfel_neve, netto_ft, brutto_ft)
                VALUES (:e,:u,:n,:b)
            """, {
                "e": kod,
                "u": ugyfel,
                "n": netto,
                "b": brutto
            })

            if ok:
                st.success(f"✅ Mentve (bruttó: {brutto:,})")

    st.dataframe(db_query("SELECT * FROM elszamolasok"))

# ============================================================
# IDŐKÖVETÉS
# ============================================================

if menu == "📱 Időkövetés":
    st.title("Időkövetés")

    projekt_lista = get_list("projektek", "projekt_szam")

    with st.form("ido"):
        proj = st.selectbox("Projekt", projekt_lista)
        ora = st.number_input("Óra", value=1.0)
        tev = st.text_input("Tevékenység")

        if st.form_submit_button("Mentés"):
            db_exec("""
                INSERT INTO idokovetes
                (projekt_szam, datum, tevekenyseg, munkaora)
                VALUES (:p,:d,:t,:m)
            """, {
                "p": proj,
                "d": str(datetime.date.today()),
                "t": sanitize(tev),
                "m": ora
            })

            st.success("Mentve")

    df = db_query("SELECT * FROM idokovetes ORDER BY datum DESC")

    if not df.empty:
        st.metric("Összes óra", f"{df['munkaora'].sum():.1f}")
        st.bar_chart(df.groupby("projekt_szam")["munkaora"].sum())
        st.dataframe(df)

