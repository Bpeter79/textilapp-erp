import re
import html
import datetime
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

APP_VERSION = "7.0"

st.set_page_config(page_title=f"TextilApp ERP v{APP_VERSION}", layout="wide")

DATABASE_URL = st.secrets["DATABASE_URL"]

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL, connect_args={"sslmode": "require"}, pool_pre_ping=True)

engine = get_engine()

def sanitize(val):
    if val is None:
        return ""
    if not isinstance(val, str):
        return str(val)
    val = re.sub(r"[\x00-\x1f\x7f]", "", val)
    return html.escape(val.strip())

def netto_to_brutto(netto, afa=27):
    n = Decimal(str(netto))
    return int((n * (Decimal("1") + Decimal(afa) / 100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def db_query(sql, params=None):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})

def db_exec(sql, params=None):
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})
    return True

def scalar(sql, params=None):
    df = db_query(sql, params)
    return df.iloc[0, 0] if not df.empty else 0

def money(x):
    try:
        return f"{int(x):,} Ft".replace(",", " ")
    except:
        return "0 Ft"

if "selected_customer_id" not in st.session_state:
    st.session_state.selected_customer_id = None

if "selected_project_id" not in st.session_state:
    st.session_state.selected_project_id = None

menu = st.sidebar.radio("Modul", [
    "📊 Dashboard",
    "🏢 Ügyfelek",
    "🚀 Projektek",
    "🖨️ Elszámolás",
    "📱 Időkövetés"
])

if menu == "📊 Dashboard":
    st.title("Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ügyfelek", scalar("SELECT COUNT(*) FROM ugyfelek"))
    c2.metric("Projektek", scalar("SELECT COUNT(*) FROM projektek"))
    c3.metric("Elszámolások", scalar("SELECT COUNT(*) FROM elszamolasok"))
    c4.metric("Időbejegyzések", scalar("SELECT COUNT(*) FROM idokovetes"))

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Utolsó projektek")
        proj_df = db_query("""
            SELECT p.id, p.projekt_szam, p.projekt_neve, u.cegnev
            FROM projektek p
            LEFT JOIN ugyfelek u ON u.id = p.ugyfel_id
            ORDER BY p.id DESC
            LIMIT 10
        """)
        st.dataframe(proj_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Gyors információ")
        st.info("A rendszer most már ID-alapú kapcsolatokkal dolgozik, így a névduplikációk nem okoznak hibát.")
        st.warning("A DB jelszót érdemes secrets-be tenni.")

if menu == "🏢 Ügyfelek":
    st.title("Ügyfelek")

    q = st.text_input("Keresés", placeholder="Cégnév, email, telefon")

    cust_sql = """
        SELECT id, cegnev, email, telefon, adoszam, varos
        FROM ugyfelek
        WHERE (:q = '' OR cegnev ILIKE :like OR email ILIKE :like OR telefon ILIKE :like)
        ORDER BY id DESC
    """
    df = db_query(cust_sql, {"q": q.strip(), "like": f"%{q.strip()}%"})

    col_a, col_b = st.columns([2, 1])

    with col_b:
        st.subheader("Új ügyfél")
        with st.form("new_customer", clear_on_submit=True):
            cegnev = st.text_input("Cégnév")
            email = st.text_input("Email")
            telefon = st.text_input("Telefon")
            adoszam = st.text_input("Adószám")
            varos = st.text_input("Város")
            submitted = st.form_submit_button("Mentés")
            if submitted:
                if not cegnev.strip():
                    st.error("A cégnév kötelező.")
                else:
                    db_exec("""
                        INSERT INTO ugyfelek (cegnev, email, telefon, adoszam, varos)
                        VALUES (:cegnev, :email, :telefon, :adoszam, :varos)
                    """, {
                        "cegnev": sanitize(cegnev),
                        "email": sanitize(email),
                        "telefon": sanitize(telefon),
                        "adoszam": sanitize(adoszam),
                        "varos": sanitize(varos),
                    })
                    st.success("Ügyfél mentve.")

    with col_a:
        st.subheader("Lista")
        st.dataframe(df, use_container_width=True, hide_index=True)

        if not df.empty:
            chosen_id = st.selectbox("Részletek", df["id"].tolist(), format_func=lambda x: f"#{x} — {df[df['id']==x]['cegnev'].iloc[0]}")
            row = df[df["id"] == chosen_id].iloc[0]

            st.markdown(f"### {row['cegnev']}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Projektek", scalar("SELECT COUNT(*) FROM projektek WHERE ugyfel_id=:id", {"id": chosen_id}))
            m2.metric("Bevétel", money(scalar("SELECT COALESCE(SUM(brutto_ft),0) FROM elszamolasok WHERE ugyfel_id=:id", {"id": chosen_id})))
            m3.metric("Óra", f"{float(scalar('SELECT COALESCE(SUM(munkaora),0) FROM idokovetes WHERE ugyfel_id=:id', {'id': chosen_id})):.1f}")

if menu == "🚀 Projektek":
    st.title("Projektek")
    ugyfelek = db_query("SELECT id, cegnev FROM ugyfelek ORDER BY cegnev")
    if ugyfelek.empty:
        st.warning("Előbb hozz létre legalább egy ügyfelet.")
    else:
        left, right = st.columns([2, 1])

        with right:
            st.subheader("Új projekt")
            with st.form("new_project", clear_on_submit=True):
                projekt_szam = st.text_input("Projekt szám")
                projekt_neve = st.text_input("Projekt neve")
                ugyfel_id = st.selectbox("Ügyfél", ugyfelek["id"].tolist(), format_func=lambda x: ugyfelek[ugyfelek["id"] == x]["cegnev"].iloc[0])
                statusz = st.selectbox("Státusz", ["Tervezés", "Folyamatban", "Kész", "Szünetel"])
                hatarido = st.date_input("Határidő")
                if st.form_submit_button("Mentés"):
                    if not projekt_szam.strip() or not projekt_neve.strip():
                        st.error("A projekt szám és név kötelező.")
                    else:
                        db_exec("""
                            INSERT INTO projektek (projekt_szam, projekt_neve, ugyfel_id, statusz, hatarido)
                            VALUES (:projekt_szam, :projekt_neve, :ugyfel_id, :statusz, :hatarido)
                        """, {
                            "projekt_szam": sanitize(projekt_szam),
                            "projekt_neve": sanitize(projekt_neve),
                            "ugyfel_id": int(ugyfel_id),
                            "statusz": statusz,
                            "hatarido": str(hatarido),
                        })
                        st.success("Projekt mentve.")

        with left:
            st.subheader("Projektlista")
            proj_df = db_query("""
                SELECT p.id, p.projekt_szam, p.projekt_neve, p.statusz, p.hatarido, u.cegnev
                FROM projektek p
                LEFT JOIN ugyfelek u ON u.id = p.ugyfel_id
                ORDER BY p.id DESC
            """)
            st.dataframe(proj_df, use_container_width=True, hide_index=True)

if menu == "🖨️ Elszámolás":
    st.title("Elszámolás")
    ugyfelek = db_query("SELECT id, cegnev FROM ugyfelek ORDER BY cegnev")
    if ugyfelek.empty:
        st.warning("Előbb hozz létre legalább egy ügyfelet.")
    else:
        with st.form("new_invoice", clear_on_submit=True):
            elsz_szam = st.text_input("Elszámolás száma")
            ugyfel_id = st.selectbox("Ügyfél", ugyfelek["id"].tolist(), format_func=lambda x: ugyfelek[ugyfelek["id"] == x]["cegnev"].iloc[0])
            netto_ft = st.number_input("Nettó Ft", min_value=0, step=1000)
            afa = st.number_input("ÁFA %", min_value=0, max_value=100, value=27)
            datum = st.date_input("Dátum")
            if st.form_submit_button("Mentés"):
                brutto = netto_to_brutto(netto_ft, afa)
                db_exec("""
                    INSERT INTO elszamolasok (elsz_szam, ugyfel_id, netto_ft, brutto_ft, afa_szazalek, datum)
                    VALUES (:elsz_szam, :ugyfel_id, :netto_ft, :brutto_ft, :afa_szazalek, :datum)
                """, {
                    "elsz_szam": sanitize(elsz_szam),
                    "ugyfel_id": int(ugyfel_id),
                    "netto_ft": int(netto_ft),
                    "brutto_ft": int(brutto),
                    "afa_szazalek": int(afa),
                    "datum": str(datum),
                })
                st.success("Elszámolás mentve.")

        inv_df = db_query("""
            SELECT e.id, e.elsz_szam, u.cegnev, e.netto_ft, e.brutto_ft, e.datum
            FROM elszamolasok e
            LEFT JOIN ugyfelek u ON u.id = e.ugyfel_id
            ORDER BY e.id DESC
        """)
        st.dataframe(inv_df, use_container_width=True, hide_index=True)

if menu == "📱 Időkövetés":
    st.title("Időkövetés")
    projektek = db_query("""
        SELECT p.id, p.projekt_szam, p.projekt_neve, u.cegnev
        FROM projektek p
        LEFT JOIN ugyfelek u ON u.id = p.ugyfel_id
        ORDER BY p.id DESC
    """)
    if projektek.empty:
        st.warning("Előbb hozz létre legalább egy projektet.")
    else:
        with st.form("new_time", clear_on_submit=True):
            projekt_id = st.selectbox("Projekt", projektek["id"].tolist(), format_func=lambda x: f"{projektek[projektek['id']==x]['projekt_szam'].iloc[0]} — {projektek[projektek['id']==x]['projekt_neve'].iloc[0]}")
            datum = st.date_input("Dátum")
            munkaora = st.number_input("Óra", min_value=0.25, step=0.25, format="%.2f")
            tevekenyseg = st.text_area("Tevékenység")
            ugyfel_id = int(scalar("SELECT ugyfel_id FROM projektek WHERE id=:id", {"id": int(projekt_id)}))
            if st.form_submit_button("Mentés"):
                db_exec("""
                    INSERT INTO idokovetes (projekt_id, ugyfel_id, datum, tevekenyseg, munkaora)
                    VALUES (:projekt_id, :ugyfel_id, :datum, :tevekenyseg, :munkaora)
                """, {
                    "projekt_id": int(projekt_id),
                    "ugyfel_id": ugyfel_id,
                    "datum": str(datum),
                    "tevekenyseg": sanitize(tevekenyseg),
                    "munkaora": float(munkaora),
                })
                st.success("Időbejegyzés mentve.")
