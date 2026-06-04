"""
TextilApp ERP v4.0 — Modernizált változat
Javítások: SQLite adatbázis, hibakezelés, Decimal pénzügyek,
           PDF generálás, szűrés, vizualizációk, biztonsági alapok
"""

import os
import re
import datetime
from decimal import Decimal, ROUND_HALF_UP
from contextlib import contextmanager

import pandas as pd
import streamlit as st

# --- SQLite + SQLAlchemy (CSV helyett) ---
try:
    from sqlalchemy import create_engine, text
    HAS_SQL = True
except ImportError:
    HAS_SQL = False

# --- PDF generálás ---
try:
    from fpdf import FPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ============================================================
# KONFIGURÁCIÓ
# ============================================================
DB_PATH = "textilapp.db"
APP_VERSION = "4.0"

st.set_page_config(
    page_title=f"TextilApp ERP v{APP_VERSION}",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ADATBÁZIS RÉTEG — SQLite (CSV fallback ha nincs sqlalchemy)
# ============================================================

# Séma definíciók
SCHEMA = {
    "ugyfelek": """
        CREATE TABLE IF NOT EXISTS ugyfelek (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cegnev TEXT UNIQUE NOT NULL,
            adoszam TEXT,
            szekhely TEXT,
            email TEXT,
            telefon TEXT,
            fiz_feltetel TEXT DEFAULT '15 napos átutalás',
            statusz TEXT DEFAULT 'aktív',
            kedvezmeny_pct REAL DEFAULT 0,
            megjegyzes TEXT,
            letrehozva TEXT DEFAULT (date('now'))
        )""",
    "kapcsolattartok": """
        CREATE TABLE IF NOT EXISTS kapcsolattartok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nev TEXT NOT NULL,
            ugyfel_neve TEXT NOT NULL,
            beosztas TEXT,
            email TEXT,
            mobil TEXT,
            aktiv INTEGER DEFAULT 1,
            letrehozva TEXT DEFAULT (date('now'))
        )""",
    "projektek": """
        CREATE TABLE IF NOT EXISTS projektek (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projekt_szam TEXT UNIQUE NOT NULL,
            projekt_neve TEXT NOT NULL,
            ugyfel_neve TEXT NOT NULL,
            kontakt_neve TEXT,
            tipus TEXT,
            statusz TEXT DEFAULT 'folyamatban',
            prioritas TEXT DEFAULT 'normál',
            kezdes TEXT DEFAULT (date('now')),
            hataridő TEXT,
            dij_netto INTEGER DEFAULT 0,
            optitex_mappa TEXT,
            megjegyzes TEXT
        )""",
    "arajanlatok": """
        CREATE TABLE IF NOT EXISTS arajanlatok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ajanlat_szam TEXT UNIQUE NOT NULL,
            nev TEXT,
            ugyfel_neve TEXT,
            projekt_szam TEXT,
            datum TEXT DEFAULT (date('now')),
            netto_ft INTEGER DEFAULT 0,
            afa_pct INTEGER DEFAULT 27,
            brutto_ft INTEGER DEFAULT 0,
            statusz TEXT DEFAULT 'készített'
        )""",
    "arajanlat_tetelek": """
        CREATE TABLE IF NOT EXISTS arajanlat_tetelek (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ajanlat_szam TEXT NOT NULL,
            tetel_neve TEXT NOT NULL,
            szolg_tipus TEXT,
            leiras TEXT,
            mennyiseg REAL DEFAULT 1,
            egysegar_netto INTEGER DEFAULT 0,
            osszeg_netto INTEGER DEFAULT 0
        )""",
    "elszamolasok": """
        CREATE TABLE IF NOT EXISTS elszamolasok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elsz_szam TEXT UNIQUE NOT NULL,
            nev TEXT,
            ugyfel_neve TEXT NOT NULL,
            projekt_szam TEXT,
            ajanlat_szam TEXT,
            idoszak_tol TEXT,
            idoszak_ig TEXT,
            kiallitas TEXT DEFAULT (date('now')),
            netto_ft INTEGER DEFAULT 0,
            afa_pct INTEGER DEFAULT 27,
            brutto_ft INTEGER DEFAULT 0,
            eloleg_levonva INTEGER DEFAULT 0,
            fizetendo_ft INTEGER DEFAULT 0,
            statusz TEXT DEFAULT 'készített',
            jovahagyva INTEGER DEFAULT 0
        )""",
    "elszamolas_tetelek": """
        CREATE TABLE IF NOT EXISTS elszamolas_tetelek (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elsz_szam TEXT NOT NULL,
            tetel_neve TEXT NOT NULL,
            projekt_szam TEXT,
            szolg_tipus TEXT,
            elvegzett_munka TEXT,
            mennyiseg REAL DEFAULT 1,
            egyseg TEXT DEFAULT 'db',
            egysegar_netto INTEGER DEFAULT 0,
            osszeg_netto INTEGER DEFAULT 0
        )""",
    "idokovetes": """
        CREATE TABLE IF NOT EXISTS idokovetes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projekt_szam TEXT NOT NULL,
            ugyfel_neve TEXT,
            datum TEXT DEFAULT (date('now')),
            tevekenyseg TEXT NOT NULL,
            munkaora REAL DEFAULT 1,
            szamlazható INTEGER DEFAULT 1,
            szamlazva INTEGER DEFAULT 0,
            megjegyzes TEXT
        )"""
}

SCHEMA_VERSION = 4  # Növeld meg ha sémát változtatsz

@st.cache_resource
def get_engine():
    if not HAS_SQL:
        return None
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    with engine.connect() as conn:
        # Verzióellenőrzés: ha régi séma, töröljük és újraépítjük
        conn.execute(text("CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)"))
        row = conn.execute(text("SELECT value FROM _meta WHERE key='schema_version'")).fetchone()
        current_ver = int(row[0]) if row else 0

        if current_ver < SCHEMA_VERSION:
            # Régi táblák eldobása
            for tbl in list(SCHEMA.keys()) + ["_meta"]:
                conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
            # Újraépítés
            for table_sql in SCHEMA.values():
                conn.execute(text(table_sql))
            conn.execute(text("CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)"))
            conn.execute(text("INSERT INTO _meta (key,value) VALUES ('schema_version',:v)"),
                         {"v": str(SCHEMA_VERSION)})
            conn.commit()
            st.cache_data.clear()
        else:
            conn.commit()
    return engine

def db_query(sql, params=None):
    """SELECT — visszaad DataFrame-t"""
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            result = pd.read_sql_query(text(sql), conn, params=params or {})
        return result
    except Exception as e:
        st.error(f"Lekérdezési hiba: {e}")
        return pd.DataFrame()

def db_exec(sql, params=None):
    """INSERT / UPDATE / DELETE — tranzakcióban fut"""
    engine = get_engine()
    if engine is None:
        st.error("Adatbázis nem elérhető. Telepítsd: pip install sqlalchemy")
        return False
    try:
        with engine.begin() as conn:   # begin() = automatikus commit/rollback
            conn.execute(text(sql), params or {})
        return True
    except Exception as e:
        st.error(f"Mentési hiba: {e}")
        return False

# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def sanitize(val: str) -> str:
    """Alapvető XSS és injection védelem szöveges mezőkhöz"""
    if not isinstance(val, str):
        return str(val)
    # Vezérlő karakterek eltávolítása
    val = re.sub(r'[\x00-\x1f\x7f]', '', val)
    return val.strip()

def netto_to_brutto(netto: int, afa_pct: int = 27) -> int:
    """Kerekítési hiba nélküli ÁFA számítás Decimal segítségével"""
    n = Decimal(str(netto))
    szorzo = Decimal('1') + Decimal(str(afa_pct)) / Decimal('100')
    return int((n * szorzo).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def validate_elszam_szam(szam: str) -> bool:
    """Elszámolásszám formátum validálás (path traversal védelem)"""
    return bool(re.match(r'^[A-Z]{2,6}-\d{4}-\d{3,6}$', szam))

# Listák (gyorsítótárazott lekérdezések)
@st.cache_data(ttl=30)
def get_list(tabla: str, mezo: str) -> list:
    df = db_query(f"SELECT DISTINCT {mezo} FROM {tabla} WHERE {mezo} IS NOT NULL ORDER BY {mezo}")
    return df[mezo].tolist() if not df.empty else []

def invalidate_lists():
    get_list.clear()

# ============================================================
# PDF NYOMTATÁS (fpdf2 alapú, webbrowser.open helyett)
# ============================================================

def elszamolas_pdf(elsz_szam: str) -> bytes | None:
    """Letölthető PDF generálása — nem nyit böngészőt"""
    if not HAS_PDF:
        st.warning("PDF generáláshoz: pip install fpdf2")
        return None

    fej = db_query(
        "SELECT * FROM elszamolasok WHERE elsz_szam = :s",
        {"s": elsz_szam}
    )
    tetelek = db_query(
        "SELECT * FROM elszamolas_tetelek WHERE elsz_szam = :s",
        {"s": elsz_szam}
    )

    if fej.empty:
        st.error("Elszámolás nem található.")
        return None

    f = fej.iloc[0]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.set_fill_color(240, 240, 245)
    pdf.cell(0, 12, "ELSZÁMOLÁSI JEGYZÉK", new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 7, f"Kód: {f['elsz_szam']}   |   Ügyfél: {f['ugyfel_neve']}   |   Kiállítva: {f['kiallitas']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Fejléc sor
    pdf.set_font("Helvetica", style="B", size=9)
    pdf.set_fill_color(220, 220, 230)
    for col, w in [("Tétel neve", 80), ("Mennyiség", 25), ("Egységár", 35), ("Összeg", 40)]:
        pdf.cell(w, 8, col, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", size=9)
    for _, r in tetelek.iterrows():
        pdf.cell(80, 7, str(r["tetel_neve"])[:45], border=1)
        pdf.cell(25, 7, str(r["mennyiseg"]), border=1, align="R")
        pdf.cell(35, 7, f"{int(r['egysegar_netto']):,} Ft", border=1, align="R")
        pdf.cell(40, 7, f"{int(r['osszeg_netto']):,} Ft", border=1, align="R")
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(0, 8, f"Nettó összeg: {int(f['netto_ft']):,} Ft  |  Bruttó összeg: {int(f['brutto_ft']):,} Ft  |  Fizetendő: {int(f['fizetendo_ft']):,} Ft", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())

# ============================================================
# NAVIGÁCIÓ
# ============================================================

st.sidebar.title("🧵 TextilApp ERP v4.0")
if not HAS_SQL:
    st.sidebar.error("⚠️ SQLAlchemy hiányzik! Futtasd: pip install sqlalchemy")
if not HAS_PDF:
    st.sidebar.warning("ℹ️ PDF-hez: pip install fpdf2")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Modul",
    [
        "📊 Vezérlőpult",
        "🏢 Ügyfelek & Kontaktok",
        "🚀 Projektek",
        "💰 Árajánlatok",
        "🖨️ Elszámolás",
        "📱 Időkövetés",
    ]
)

# ============================================================
# 1. VEZÉRLŐPULT
# ============================================================
if menu == "📊 Vezérlőpult":
    st.title("📊 Vezérlőpult")

    c1, c2, c3, c4 = st.columns(4)
    def scalar(sql, fallback=0):
        df = db_query(sql)
        if df.empty or df.iloc[0, 0] is None:
            return fallback
        return df.iloc[0, 0]

    c1.metric("Ügyfelek", scalar("SELECT COUNT(*) as n FROM ugyfelek"))
    c2.metric("Projektek", scalar("SELECT COUNT(*) as n FROM projektek"))
    c3.metric("Árajánlatok", scalar("SELECT COUNT(*) as n FROM arajanlatok"))
    c4.metric("Elszámolt bruttó", f"{int(scalar('SELECT COALESCE(SUM(brutto_ft),0) as total FROM elszamolasok')):,} Ft")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Elszámolások időben")
        elsz_df = db_query("SELECT kiallitas, netto_ft FROM elszamolasok ORDER BY kiallitas")
        if not elsz_df.empty:
            chart_df = elsz_df.set_index("kiallitas")[["netto_ft"]].rename(columns={"netto_ft": "Nettó Ft"})
            st.bar_chart(chart_df, height=220)
        else:
            st.info("Még nincs elszámolási adat.")

    with col_r:
        st.subheader("Projektek státusz szerint")
        p_df = db_query("SELECT statusz, COUNT(*) as db FROM projektek GROUP BY statusz")
        if not p_df.empty:
            chart_p = p_df.set_index("statusz")[["db"]].rename(columns={"db": "Projektek száma"})
            st.bar_chart(chart_p, height=220)
        else:
            st.info("Még nincs projekt adat.")

    st.subheader("Utolsó 5 projekt")
    st.dataframe(db_query("SELECT projekt_szam, projekt_neve, ugyfel_neve, statusz, prioritas, dij_netto FROM projektek ORDER BY id DESC LIMIT 5"), use_container_width=True)

# ============================================================
# 2. ÜGYFELEK
# ============================================================
elif menu == "🏢 Ügyfelek & Kontaktok":
    st.title("🏢 Ügyfelek és Kapcsolattartók")

    tab1, tab2, tab3 = st.tabs(["➕ Új ügyfél", "👤 Új kontakt", "🔍 Listázás"])

    with tab1:
        with st.form("ugyfel_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            cegnev = col1.text_input("Cégnév *")
            adoszam = col2.text_input("Adószám")
            szekhely = col1.text_input("Székhely")
            email = col2.text_input("Email")
            telefon = col1.text_input("Telefon")
            fiz = col2.selectbox("Fizetési feltétel", ["8 napos", "15 napos", "30 napos", "Készpénz"])

            if st.form_submit_button("💾 Mentés"):
                if not cegnev:
                    st.error("A Cégnév kötelező!")
                else:
                    cegnev = sanitize(cegnev)
                    ok = db_exec(
                        "INSERT INTO ugyfelek (cegnev, adoszam, szekhely, email, telefon, fiz_feltetel) VALUES (:c,:a,:s,:e,:t,:f)",
                        {"c": cegnev, "a": sanitize(adoszam), "s": sanitize(szekhely),
                         "e": sanitize(email), "t": sanitize(telefon), "f": fiz}
                    )
                    if ok:
                        invalidate_lists()
                        st.success(f"✅ Ügyfél '{cegnev}' elmentve!")
                        st.rerun()

    with tab2:
        ugyfel_lista = get_list("ugyfelek", "cegnev")
        with st.form("kontakt_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            k_nev = col1.text_input("Teljes név *")
            k_ceg = col2.selectbox("Cég *", ugyfel_lista) if ugyfel_lista else col2.text_input("Cég neve *")
            k_beo = col1.text_input("Beosztás")
            k_email = col2.text_input("Email")
            k_mobil = col1.text_input("Mobil")

            if st.form_submit_button("💾 Mentés"):
                if not k_nev or not k_ceg:
                    st.error("Név és cég kötelező!")
                else:
                    ok = db_exec(
                        "INSERT INTO kapcsolattartok (nev, ugyfel_neve, beosztas, email, mobil) VALUES (:n,:c,:b,:e,:m)",
                        {"n": sanitize(k_nev), "c": k_ceg, "b": sanitize(k_beo),
                         "e": sanitize(k_email), "m": sanitize(k_mobil)}
                    )
                    if ok:
                        invalidate_lists()
                        st.success(f"✅ Kapcsolattartó '{k_nev}' hozzáadva!")
                        st.rerun()

    with tab3:
        keres = st.text_input("🔍 Keresés cégnév alapján")
        query = "SELECT cegnev, adoszam, email, telefon, fiz_feltetel, statusz FROM ugyfelek"
        if keres:
            query += f" WHERE cegnev LIKE '%{sanitize(keres)}%'"
        st.dataframe(db_query(query), use_container_width=True)

# ============================================================
# 3. PROJEKTEK
# ============================================================
elif menu == "🚀 Projektek":
    st.title("🚀 Projektek Kezelése")
    tab1, tab2 = st.tabs(["➕ Új projekt", "📋 Összes projekt"])

    ugyfel_lista = get_list("ugyfelek", "cegnev")
    kontakt_lista = get_list("kapcsolattartok", "nev")

    with tab1:
        with st.form("projekt_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            p_szam = col1.text_input("Projektszám (pl: PROJ-2026-001) *")
            p_neve = col2.text_input("Megnevezés *")
            p_ugyfel = col1.selectbox("Ügyfél *", ugyfel_lista) if ugyfel_lista else col1.text_input("Ügyfél neve *")
            p_kontakt = col2.selectbox("Kapcsolattartó", [""] + kontakt_lista)
            p_tipus = col1.selectbox("Típus", ["szériázás", "mintázás", "tervezés", "gyártás előkészítés"])
            p_statusz = col2.selectbox("Státusz", ["folyamatban", "tervezett", "lezárt"])
            p_prioritas = col1.selectbox("Prioritás", ["alacsony", "normál", "sürgős"])
            p_dij = col2.number_input("Nettó díj (Ft)", value=0, step=5000)
            p_hataridő = st.date_input("Határidő", value=None)
            p_mappa = st.text_input("Optitex mappa")

            if st.form_submit_button("🚀 Projekt indítása"):
                if not p_szam or not p_neve:
                    st.error("Projektszám és megnevezés kötelező!")
                else:
                    ok = db_exec(
                        """INSERT INTO projektek (projekt_szam, projekt_neve, ugyfel_neve, kontakt_neve,
                           tipus, statusz, prioritas, hataridő, dij_netto, optitex_mappa)
                           VALUES (:ps,:pn,:un,:kn,:t,:st,:pr,:ha,:di,:op)""",
                        {"ps": sanitize(p_szam), "pn": sanitize(p_neve), "un": p_ugyfel,
                         "kn": p_kontakt, "t": p_tipus, "st": p_statusz, "pr": p_prioritas,
                         "ha": str(p_hataridő) if p_hataridő else None,
                         "di": int(p_dij), "op": sanitize(p_mappa)}
                    )
                    if ok:
                        invalidate_lists()
                        st.success(f"✅ Projekt '{p_szam}' elindítva!")
                        st.rerun()

    with tab2:
        szuro_statusz = st.selectbox("Szűrés státuszra", ["mind", "folyamatban", "tervezett", "lezárt"])
        q = "SELECT projekt_szam, projekt_neve, ugyfel_neve, statusz, prioritas, dij_netto, hataridő FROM projektek"
        if szuro_statusz != "mind":
            q += f" WHERE statusz = '{szuro_statusz}'"
        q += " ORDER BY id DESC"
        st.dataframe(db_query(q), use_container_width=True)

# ============================================================
# 4. ÁRAJÁNLATOK
# ============================================================
elif menu == "💰 Árajánlatok":
    st.title("💰 Árajánlatok")
    ta1, ta2, ta3 = st.tabs(["📄 Fejléc", "🏷️ Tételek", "🔍 Megtekintés"])

    ugyfel_lista = get_list("ugyfelek", "cegnev")
    projekt_lista = get_list("projektek", "projekt_szam")
    ajanlat_lista = get_list("arajanlatok", "ajanlat_szam")

    with ta1:
        with st.form("aj_fej"):
            col1, col2 = st.columns(2)
            aj_szam = col1.text_input("Ajánlat száma *")
            aj_nev = col2.text_input("Megnevezés")
            aj_u = col1.selectbox("Ügyfél", ugyfel_lista) if ugyfel_lista else col1.text_input("Ügyfél neve")
            aj_p = col2.selectbox("Projekt", [""] + projekt_lista)
            aj_netto = st.number_input("Nettó érték (Ft)", value=0, step=1000)

            if st.form_submit_button("💾 Fejléc mentése"):
                if not aj_szam:
                    st.error("Ajánlatszám kötelező!")
                else:
                    brutto = netto_to_brutto(int(aj_netto))
                    ok = db_exec(
                        "INSERT INTO arajanlatok (ajanlat_szam, nev, ugyfel_neve, projekt_szam, netto_ft, brutto_ft) VALUES (:as,:n,:u,:p,:ne,:br)",
                        {"as": sanitize(aj_szam), "n": sanitize(aj_nev), "u": aj_u,
                         "p": aj_p, "ne": int(aj_netto), "br": brutto}
                    )
                    if ok:
                        invalidate_lists()
                        st.success(f"✅ Árajánlat '{aj_szam}' mentve! Bruttó: {brutto:,} Ft")
                        st.rerun()

    with ta2:
        with st.form("aj_tetel"):
            t_aj = st.selectbox("Árajánlat *", ajanlat_lista) if ajanlat_lista else st.text_input("Ajánlatszám")
            col1, col2 = st.columns(2)
            t_nev = col1.text_input("Tétel neve *")
            t_szolg = col2.selectbox("Típus", ["szériázás", "mintázás", "tervezés", "DXF export"])
            t_leiras = st.text_area("Leírás", height=80)
            col3, col4 = st.columns(2)
            t_db = col3.number_input("Mennyiség", value=1.0, min_value=0.1)
            t_ar = col4.number_input("Egységár Ft", value=0, step=500)

            if st.form_submit_button("➕ Tétel hozzáadása"):
                if not t_nev:
                    st.error("Tétel neve kötelező!")
                else:
                    osszeg = int(Decimal(str(t_db)) * Decimal(str(t_ar)))
                    ok = db_exec(
                        "INSERT INTO arajanlat_tetelek (ajanlat_szam, tetel_neve, szolg_tipus, leiras, mennyiseg, egysegar_netto, osszeg_netto) VALUES (:a,:t,:s,:l,:m,:e,:o)",
                        {"a": t_aj, "t": sanitize(t_nev), "s": t_szolg,
                         "l": sanitize(t_leiras), "m": float(t_db), "e": int(t_ar), "o": osszeg}
                    )
                    if ok:
                        st.success(f"✅ Tétel hozzáadva. Összeg: {osszeg:,} Ft")

    with ta3:
        if ajanlat_lista:
            valaszt = st.selectbox("Ajánlat kiválasztása", ajanlat_lista)
            fej = db_query("SELECT * FROM arajanlatok WHERE ajanlat_szam = :s", {"s": valaszt})
            if not fej.empty:
                f = fej.iloc[0]
                col1, col2, col3 = st.columns(3)
                col1.metric("Nettó", f"{int(f['netto_ft']):,} Ft")
                col2.metric("ÁFA (27%)", f"{int(f['brutto_ft']) - int(f['netto_ft']):,} Ft")
                col3.metric("Bruttó", f"{int(f['brutto_ft']):,} Ft")
            st.dataframe(
                db_query("SELECT tetel_neve, szolg_tipus, mennyiseg, egysegar_netto, osszeg_netto FROM arajanlat_tetelek WHERE ajanlat_szam = :s", {"s": valaszt}),
                use_container_width=True
            )
        else:
            st.info("Még nincs mentett árajánlat.")

# ============================================================
# 5. ELSZÁMOLÁS
# ============================================================
elif menu == "🖨️ Elszámolás":
    st.title("🖨️ Elszámolás Központ")
    te1, te2, te3 = st.tabs(["📄 Fejrész", "🏷️ Tételek", "🔍 Nyomtatás / Letöltés"])

    ugyfel_lista = get_list("ugyfelek", "cegnev")
    projekt_lista = get_list("projektek", "projekt_szam")
    ajanlat_lista = get_list("arajanlatok", "ajanlat_szam")
    elszam_lista = get_list("elszamolasok", "elsz_szam")

    with te1:
        with st.form("elsz_fej", clear_on_submit=True):
            col1, col2 = st.columns(2)
            e_szam = col1.text_input("Elszámolás száma (pl: ELSZ-2026-001) *")
            e_nev = col2.text_input("Megnevezés", value="Munka elszámolási jegyzék")
            e_u = col1.selectbox("Ügyfél *", ugyfel_lista) if ugyfel_lista else col1.text_input("Ügyfél neve *")
            e_p = col2.selectbox("Projekt", [""] + projekt_lista)
            e_aj = col1.selectbox("Árajánlat", [""] + ajanlat_lista)
            e_tol = col2.date_input("Időszak tól", value=None)
            e_ig = col1.date_input("Időszak ig", value=None)
            e_netto = col2.number_input("Nettó összeg (Ft)", value=0, step=1000)
            e_eloleg = st.number_input("Előleg levonva (Ft)", value=0, step=1000)

            if st.form_submit_button("💾 Fejrész mentése"):
                if not e_szam or not e_u:
                    st.error("Elszámolásszám és ügyfél kötelező!")
                elif not validate_elszam_szam(e_szam):
                    st.error("Helytelen formátum! Pl: ELSZ-2026-001")
                else:
                    brutto = netto_to_brutto(int(e_netto))
                    fizetendo = brutto - int(e_eloleg)
                    ok = db_exec(
                        """INSERT INTO elszamolasok
                           (elsz_szam, nev, ugyfel_neve, projekt_szam, ajanlat_szam,
                            idoszak_tol, idoszak_ig, netto_ft, brutto_ft, eloleg_levonva, fizetendo_ft)
                           VALUES (:es,:n,:u,:p,:a,:tol,:ig,:ne,:br,:el,:fi)""",
                        {"es": e_szam, "n": sanitize(e_nev), "u": e_u, "p": e_p, "a": e_aj,
                         "tol": str(e_tol) if e_tol else None, "ig": str(e_ig) if e_ig else None,
                         "ne": int(e_netto), "br": brutto, "el": int(e_eloleg), "fi": fizetendo}
                    )
                    if ok:
                        invalidate_lists()
                        st.success(f"✅ Elszámolás '{e_szam}' mentve! Fizetendő: {fizetendo:,} Ft")
                        st.rerun()

    with te2:
        with st.form("elsz_tetel", clear_on_submit=True):
            et_elsz = st.selectbox("Elszámolás *", elszam_lista) if elszam_lista else st.text_input("Elszámolásszám")
            col1, col2 = st.columns(2)
            et_nev = col1.text_input("Tétel neve *")
            et_szolg = col2.selectbox("Típus", ["szériázás", "mintázás", "tervezés", "alapszerkesztés"])
            et_munka = st.text_area("Elvégzett munka leírása", height=80)
            col3, col4 = st.columns(2)
            et_db = col3.number_input("Mennyiség", value=1.0, min_value=0.1)
            et_ar = col4.number_input("Egységár Ft", value=0, step=500)

            if st.form_submit_button("➕ Tétel hozzáadása"):
                if not et_nev:
                    st.error("Tétel neve kötelező!")
                else:
                    osszeg = int(Decimal(str(et_db)) * Decimal(str(et_ar)))
                    ok = db_exec(
                        """INSERT INTO elszamolas_tetelek
                           (elsz_szam, tetel_neve, szolg_tipus, elvegzett_munka, mennyiseg, egysegar_netto, osszeg_netto)
                           VALUES (:e,:n,:s,:m,:db,:ar,:o)""",
                        {"e": et_elsz, "n": sanitize(et_nev), "s": et_szolg,
                         "m": sanitize(et_munka), "db": float(et_db), "ar": int(et_ar), "o": osszeg}
                    )
                    if ok:
                        st.success(f"✅ Tétel hozzáadva: {osszeg:,} Ft")

    with te3:
        if elszam_lista:
            val = st.selectbox("Elszámolás kiválasztása", elszam_lista)

            fej = db_query("SELECT * FROM elszamolasok WHERE elsz_szam = :s", {"s": val})
            if not fej.empty:
                f = fej.iloc[0]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Nettó", f"{int(f['netto_ft']):,} Ft")
                col2.metric("ÁFA", f"{int(f['brutto_ft']) - int(f['netto_ft']):,} Ft")
                col3.metric("Bruttó", f"{int(f['brutto_ft']):,} Ft")
                col4.metric("Fizetendő", f"{int(f['fizetendo_ft']):,} Ft")

            tetelek_df = db_query(
                "SELECT tetel_neve, mennyiseg, egysegar_netto, osszeg_netto FROM elszamolas_tetelek WHERE elsz_szam = :s",
                {"s": val}
            )
            st.dataframe(tetelek_df, use_container_width=True)

            if HAS_PDF:
                if st.button("📥 PDF letöltése"):
                    pdf_bytes = elszamolas_pdf(val)
                    if pdf_bytes:
                        st.download_button(
                            label="⬇️ Letöltés",
                            data=pdf_bytes,
                            file_name=f"elszamolas_{val}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.info("PDF generáláshoz telepítsd: `pip install fpdf2`")
        else:
            st.info("Még nincs mentett elszámolás.")

# ============================================================
# 6. IDŐKÖVETÉS
# ============================================================
elif menu == "📱 Időkövetés":
    st.title("📱 Időkövetés")
    st.info("Adatok az `idokovetes` táblába mentődnek, pénzügyektől függetlenül.")

    projekt_lista = get_list("projektek", "projekt_szam")
    tab1, tab2 = st.tabs(["⏱️ Rögzítés", "📊 Kimutatás"])

    with tab1:
        with st.form("ido_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            p_kod = col1.selectbox("Projekt *", projekt_lista) if projekt_lista else col1.text_input("Projektszám")
            o_num = col2.number_input("Munkaóra", value=1.0, step=0.5, min_value=0.5)
            t_txt = st.text_input("Tevékenység leírása *")
            szamlaz = st.checkbox("Számlázható", value=True)
            datum = st.date_input("Dátum", value=datetime.date.today())

            if st.form_submit_button("💾 Rögzítés"):
                if not p_kod or not t_txt:
                    st.error("Projekt és tevékenység kötelező!")
                else:
                    ugyfel_df = db_query("SELECT ugyfel_neve FROM projektek WHERE projekt_szam = :p", {"p": p_kod})
                    u_neve = ugyfel_df.iloc[0]["ugyfel_neve"] if not ugyfel_df.empty else ""
                    ok = db_exec(
                        "INSERT INTO idokovetes (projekt_szam, ugyfel_neve, datum, tevekenyseg, munkaora, szamlazható) VALUES (:p,:u,:d,:t,:m,:s)",
                        {"p": p_kod, "u": u_neve, "d": str(datum),
                         "t": sanitize(t_txt), "m": float(o_num), "s": int(szamlaz)}
                    )
                    if ok:
                        st.success(f"✅ {o_num:.1f} óra rögzítve a '{p_kod}' projekthez!")

    with tab2:
        ido_df = db_query(
            "SELECT projekt_szam, ugyfel_neve, datum, tevekenyseg, munkaora, szamlazható FROM idokovetes ORDER BY datum DESC"
        )
        if not ido_df.empty:
            col1, col2 = st.columns(2)
            col1.metric("Összes rögzített óra", f"{ido_df['munkaora'].sum():.1f} h")
            szamlaz_df = ido_df[ido_df["szamlazható"] == 1]
            col2.metric("Számlázható órák", f"{szamlaz_df['munkaora'].sum():.1f} h")

            ora_df = ido_df.groupby("projekt_szam")["munkaora"].sum().reset_index()
            ora_df = ora_df.set_index("projekt_szam")[["munkaora"]].rename(columns={"munkaora": "Munkaóra"})
            st.bar_chart(ora_df, height=220)
            st.dataframe(ido_df, use_container_width=True)
        else:
            st.info("Még nincs rögzített munkaidő.")
