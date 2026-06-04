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

    st.title("🏢 Ügyfél kezelő központ")

    # ==========================================================
    # TOP KPI
    # ==========================================================
    c1, c2, c3 = st.columns(3)

    def scalar(q):
        df = db_query(q)
        return df.iloc[0, 0] if not df.empty else 0

    c1.metric("📊 Ügyfelek száma", scalar("SELECT COUNT(*) FROM ugyfelek"))

    c2.metric("💰 Össz bevétel",
        f"{int(scalar('SELECT COALESCE(SUM(brutto_ft),0) FROM elszamolasok')):,} Ft"
    )

    c3.metric("📁 Aktív projektek",
        scalar("SELECT COUNT(*) FROM projektek WHERE statusz = 'folyamatban'")
    )

    st.markdown("---")

    # ==========================================================
    # SZŰRÉS + KERESÉS
    # ==========================================================
    col1, col2 = st.columns(2)

    keres = col1.text_input("🔍 Keresés cégnévre")
    iparag_filter = col2.selectbox(
        "Iparág szűrés",
        ["Összes"] + get_list("ugyfelek", "iparag")
    )

    query = "SELECT * FROM ugyfelek WHERE 1=1"

    params = {}

    if keres:
        query += " AND cegnev ILIKE :k"
        params["k"] = f"%{keres}%"

    if iparag_filter != "Összes":
        query += " AND iparag = :i"
        params["i"] = iparag_filter

    query += " ORDER BY cegnev"

    df = db_query(query, params)

    # ==========================================================
    # KÁRTYÁS NÉZET
    # ==========================================================
    st.subheader("📇 Ügyfél lista")

    if not df.empty:

        for i in range(0, len(df), 2):
            cols = st.columns(2)

            for col, (_, row) in zip(cols, df.iloc[i:i+2].iterrows()):

                ceg = row["cegnev"]
                email = row.get("email", "")
                telefon = row.get("telefon", "")
                iparag = row.get("iparag", "")
                fizetes = row.get("fizetesi_feltetel", "")

                with col:
                    st.markdown(f"""
                    ### 🏢 {ceg}
                    **📧 Email:** {email or '-'}  
                    **📞 Telefon:** {telefon or '-'}  
                    **🏭 Iparág:** {iparag or '-'}  
                    **💳 Fizetés:** {fizetes or '-'}
                    """)

                    # ügyfél KPI
                    proj = scalar(f"""
                        SELECT COUNT(*) FROM projektek
                        WHERE ugyfel_neve = '{ceg}'
                    """)

                    bev = scalar(f"""
                        SELECT COALESCE(SUM(brutto_ft),0)
                        FROM elszamolasok
                        WHERE ugyfel_neve = '{ceg}'
                    """)

                    ora = scalar(f"""
                        SELECT COALESCE(SUM(munkaora),0)
                        FROM idokovetes
                        WHERE ugyfel_neve = '{ceg}'
                    """)

                    st.caption(f"📁 Projektek: {proj}")
                    st.caption(f"💰 Bevétel: {int(bev):,} Ft")
                    st.caption(f"⏱️ Munkaórák: {float(ora):.1f} h")

                    if st.button(f"Részletek – {ceg}", key=f"btn_{ceg}"):
                        st.session_state["selected_customer"] = ceg

                    st.markdown("---")

    else:
        st.info("Nincs találat.")

    # ==========================================================
    # RÉSZLET NÉZET
    # ==========================================================
    if "selected_customer" in st.session_state:

        ceg = st.session_state["selected_customer"]

        st.markdown("## 🔎 Ügyfél részletek")
        st.write(f"**Kiválasztva:** {ceg}")

        adat = db_query("""
            SELECT * FROM ugyfelek WHERE cegnev = :c
        """, {"c": ceg})

        if not adat.empty:
            r = adat.iloc[0]

            col1, col2 = st.columns(2)

            col1.write(f"📧 Email: {r.get('email','-')}")
            col1.write(f"📞 Telefon: {r.get('telefon','-')}")
            col1.write(f"🌐 Web: {r.get('weboldal','-')}")

            col2.write(f"🏭 Iparág: {r.get('iparag','-')}")
            col2.write(f"💳 Fizetés: {r.get('fizetesi_feltetel','-')}")
            col2.write(f"💸 Kedvezmény: {r.get('kedvezmeny_pct',0)} %")

        # projektek
        st.subheader("📁 Projektek")
        st.dataframe(db_query("""
            SELECT projekt_szam, projekt_neve, statusz
            FROM projektek
            WHERE ugyfel_neve = :c
        """, {"c": ceg}))

        # elszámolások
        st.subheader("💰 Elszámolások")
        st.dataframe(db_query("""
            SELECT elsz_szam, brutto_ft, kiallitas
            FROM elszamolasok
            WHERE ugyfel_neve = :c
        """, {"c": ceg}))

        # idő grafikon
        st.subheader("⏱️ Munkaórák")

        ido = db_query("""
            SELECT datum, munkaora
            FROM idokovetes
            WHERE ugyfel_neve = :c
        """, {"c": ceg})

        if not ido.empty:
            ido["datum"] = pd.to_datetime(ido["datum"])
            st.line_chart(ido.set_index("datum"))

        if st.button("❌ Bezár"):
            del st.session_state["selected_customer"]
            st.rerun()



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

