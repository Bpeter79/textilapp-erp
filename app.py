import streamlit as st
from db import get_all_companies, insert_company, insert_project

st.set_page_config(page_title="Optitex ERP", layout="wide")
st.sidebar.title("Navigáció")
menu = st.sidebar.radio("Válassz:", ["Ügyfélközpont", "Új Ügyfél felvitele", "Új Projekt felvitele"])

# --- ÜGYFÉLKÖZPONT ---
if menu == "Ügyfélközpont":
    st.title("🏢 Ügyfélközpont")
    # Itt jelenítsd meg a cégek listáját...

# --- ÚJ ÜGYFÉL ---
elif menu == "Új Ügyfél felvitele":
    st.title("➕ Új Ügyfél rögzítése")
    with st.form("uj_ceg"):
        n = st.text_input("Cég neve")
        t = st.text_input("Adószám")
        a = st.text_area("Cím")
        if st.form_submit_button("Cég mentése"):
            insert_company(n, t, a)
            st.success("Cég rögzítve!")

# --- ÚJ PROJEKT ---
elif menu == "Új Projekt felvitele":
    st.title("🚀 Új Projekt indítása")
    cegek = get_all_companies()
    ceg_dict = {c['name']: c['id'] for c in cegek}
    
    with st.form("uj_projekt"):
        sel_ceg = st.selectbox("Válassz ügyfelet:", list(ceg_dict.keys()))
        p_name = st.text_input("Projekt neve")
        stat = st.selectbox("Állapot", ["Tervezés", "Folyamatban", "Kész"])
        dead = st.date_input("Határidő")
        
        if st.form_submit_button("Projekt mentése"):
            insert_project(ceg_dict[sel_ceg], p_name, stat, str(dead))
            st.success("Projekt rögzítve!")
