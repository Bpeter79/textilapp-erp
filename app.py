import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Adatbázis kapcsolat (a secretsből olvas)
db_url = st.secrets["DATABASE_URL"]
engine = create_engine(db_url)

st.title("Textil ERP - Ügyfélkezelő")

# 1. Ügyfél választó és Kapcsolattartó rögzítő
st.subheader("Új kapcsolattartó hozzáadása")

# Ügyfelek lekérdezése a menühöz
ugyfelek_df = pd.read_sql("SELECT id, cegnev FROM ugyfelek", engine)
ugyfel_dict = dict(zip(ugyfelek_df['cegnev'], ugyfelek_df['id']))

selected_ceg = st.selectbox("Válassz ügyfelet:", list(ugyfel_dict.keys()))

with st.form("kapcsolat_form"):
    nev = st.text_input("Név")
    email = st.text_input("Email")
    submit = st.form_submit_button("Mentés")

    if submit:
        ugyfel_id = ugyfel_dict[selected_ceg]
        # SQL beszúrás a kapcsolattartók táblába
        with engine.connect() as conn:
            conn.execute(
                "INSERT INTO kapcsolattartok (ugyfel_id, nev, email) VALUES (%s, %s, %s)",
                (ugyfel_id, nev, email)
            )
            conn.commit()
        st.success(f"Sikeresen rögzítve ehhez a céghez: {selected_ceg}")

# 2. Megjelenítés: Ügyfelek és kapcsolataik
st.subheader("Partnerek listája")
query = """
SELECT u.cegnev, k.nev, k.email 
FROM ugyfelek u 
JOIN kapcsolattartok k ON u.id = k.ugyfel_id
"""
partnerek = pd.read_sql(query, engine)
st.dataframe(partnerek)
