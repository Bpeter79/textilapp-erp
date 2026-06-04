import streamlit as st
import pandas as pd
from db import get_all_companies, get_contacts_by_company # Ezeket a függvényeket a db.py-ban kiegészítettük

st.set_page_config(page_title="Optitex Pro ERP", layout="wide")

menu = st.sidebar.radio("Navigáció", ["Ügyfélközpont", "Új Ügyfél/Projekt felvitele"])

if menu == "Ügyfélközpont":
    st.title("🏢 Ügyfélközpont")
    cegek = get_all_companies()
    
    if cegek:
        # Ügyfélválasztó
        ceg_nevek = [c['name'] for c in cegek]
        selected_name = st.selectbox("Válassz ügyfelet:", ceg_nevek)
        c = next(item for item in cegek if item['name'] == selected_name)
        
        # Grid megjelenítés
        tab1, tab2, tab3 = st.tabs(["Cég adatok", "Kapcsolattartók", "Projektek"])
        
        with tab1:
            st.metric("Cégnév", c['name'])
            st.write(f"**Adószám:** {c.get('tax_number')}")
            st.write(f"**Székhely:** {c.get('address')}")
            
        with tab2:
            st.subheader("Kapcsolattartók")
            kontakto = get_contacts_by_company(c['id'])
            if kontakto:
                st.table(pd.DataFrame(kontakto))
            else:
                st.info("Nincs rögzítve kapcsolattartó.")
                
        with tab3:
            st.subheader("Aktív Projektek")
            # Ide jöhet a projektek lekérdezése...
    else:
        st.warning("Még nincsenek cégek az adatbázisban.")
