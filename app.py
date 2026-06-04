import streamlit as st
import pandas as pd
from db import get_all_companies, insert_company

st.set_page_config(page_title="Optitex ERP", layout="wide")

# Egyedi stílus a "belesimuló" megjelenéshez
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("Navigáció")
menu = st.sidebar.radio("Válassz:", ["Kezdőlap", "Ügyfélkezelő", "Új Ügyfél Felvétele"])

if menu == "Kezdőlap":
    st.title("👗 Optitex Szerkesztő és Ügyfélkezelő")
    st.write("Üdvözöllek! Ez a központi felület az üzleti folyamataidhoz.")
    
elif menu == "Ügyfélkezelő":
    st.subheader("Ügyfél adatbázis")
    cegek = get_all_companies()
    
    if cegek:
        df = pd.DataFrame(cegek)
        # Tisztítás: csak azokat mutatjuk, amiknek van neve
        df_clean = df[df['name'].notna() & (df['name'] != '')]
        
        st.dataframe(df_clean.drop(columns=['id']), use_container_width=True)
        
        st.write("---")
        selected_name = st.selectbox("Részletek megtekintése:", df_clean['name'].unique())
        
        c = next(item for item in cegek if item["name"] == selected_name)
        
        # Grid megjelenítés
        col1, col2 = st.columns(2)
        col1.metric("Cég neve", c['name'])
        col2.write(f"**Adószám:** {c.get('tax_number', 'Nincs megadva')}")
        st.write(f"**Cím:** {c.get('address', 'Nincs megadva')}")
        
        # Extra adatok elegáns megjelenítése
        if c.get('extra_data'):
            st.subheader("Egyéb adatok")
            for key, val in c['extra_data'].items():
                if val: # Csak akkor írjuk ki, ha nem üres
                    st.info(f"**{key}:** {val}")
    else:
        st.warning("Még nincsenek rögzített cégek.")

elif menu == "Új Ügyfél Felvétele":
    st.subheader("Új Ügyfél rögzítése")
    with st.form("ceg_mentes"):
        n = st.text_input("Cég neve*")
        t = st.text_input("Adószám")
        a = st.text_area("Cím")
        
        col1, col2 = st.columns(2)
        k = col1.text_input("Egyedi adat mező (pl. Weboldal)")
        v = col2.text_input("Érték")
        
        if st.form_submit_button("Mentés"):
            if n:
                insert_company(n, t, a, {k: v} if k else {})
                st.success("Sikeresen rögzítve!")
                st.rerun()
            else:
                st.error("A Cég neve mező kitöltése kötelező!")
