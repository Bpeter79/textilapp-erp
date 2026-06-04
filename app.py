import streamlit as st
import pandas as pd
from db import get_all_companies, insert_company, get_contacts_by_company, insert_contact

st.set_page_config(page_title="Optitex ERP", layout="wide")

st.sidebar.title("Navigáció")
menu = st.sidebar.radio("Válassz:", ["Kezdőlap", "Ügyfélkezelő", "Új adatok"])

if menu == "Kezdőlap":
    st.title("Üdvözöllek, Optitex Felhasználó! 👋")
    st.markdown("""
    Ez a központi vezérlőpult az ügyfeleid és projektjeid kezelésére. 
    A bal oldali menüből navigálhatsz a funkciók között.
    """)
    st.info("💡 Tipp: Használd az 'Ügyfélkezelő'-t a meglévő adatok szűrésére és megtekintésére.")

elif menu == "Ügyfélkezelő":
    st.subheader("Ügyfél adatbázis")
    cegek = get_all_companies()
    
    if cegek:
        df = pd.DataFrame(cegek)
        # Rejtsük el az id-t a szebb megjelenésért
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
        
        selected_name = st.selectbox("Válassz ügyfelet részletekhez:", df['name'].unique())
        c = next(item for item in cegek if item["name"] == selected_name)
        
        col1, col2 = st.columns(2)
        col1.metric("Adószám", c['tax_number'])
        col2.write(f"**Cím:** {c['address']}")
        st.json(c['extra_data'])
    else:
        st.warning("Még nincsenek rögzített cégek.")

elif menu == "Új adatok":
    tab1, tab2 = st.tabs(["Új Cég", "Új Kapcsolattartó"])
    with tab1:
        with st.form("ceg_mentes"):
            n = st.text_input("Cég neve*")
            t = st.text_input("Adószám")
            a = st.text_area("Cím")
            k = st.text_input("Egyedi adat neve (pl. Weboldal)")
            v = st.text_input("Érték")
            if st.form_submit_button("Mentés"):
                if n:
                    insert_company(n, t, a, {k: v} if k else {})
                    st.success("Mentve!")
                else: st.error("A név kötelező!")

    with tab2:
        # Kapcsolattartó kódja ide...
        pass
