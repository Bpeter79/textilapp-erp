
import streamlit as st
import pandas as pd
from db import get_all_companies, insert_company, insert_contact, get_contacts_by_company

st.set_page_config(page_title="Optitex ERP System", layout="wide")
st.title("👗 Optitex Szerkesztő és Ügyfélkezelő Rendszer")

# Oldalsáv navigáció
menu = st.sidebar.radio("Navigáció", ["Ügyfélkezelő", "Új Ügyfél / Kapcsolattartó"])

if menu == "Ügyfélkezelő":
    st.subheader("Ügyfél adatbázis")
    cegek = get_all_companies()
    
    if cegek:
        df = pd.DataFrame(cegek)
        st.dataframe(df, use_container_width=True)
        
        # Részletes nézet választóval
        selected_company_name = st.selectbox("Válassz ügyfelet a részletekhez:", df['name'].tolist())
        selected_company = next(c for c in cegek if c['name'] == selected_company_name)
        
        st.write(f"**Cím:** {selected_company['address']}")
        st.write(f"**Extra adatok:** {selected_company['extra_data']}")
        
        st.subheader("Kapcsolattartók")
        kontakto = get_contacts_by_company(selected_company['id'])
        if kontakto:
            st.table(pd.DataFrame(kontakto))
        else:
            st.warning("Nincs hozzárendelt kapcsolattartó.")

elif menu == "Új Ügyfél / Kapcsolattartó":
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Új Ügyfél rögzítése")
        with st.form("ceg_form"):
            n = st.text_input("Cég neve")
            t = st.text_input("Adószám")
            a = st.text_area("Cím")
            k = st.text_input("Extra mező neve (pl. Weboldal)")
            v = st.text_input("Extra mező értéke")
            if st.form_submit_button("Cég mentése"):
                insert_company(n, t, a, {k: v} if k else {})
                st.rerun()

    with col2:
        st.subheader("Új Kapcsolattartó hozzáadása")
        cegek = get_all_companies()
        ceg_dict = {c['name']: c['id'] for c in cegek}
        
        selected = st.selectbox("Cég kiválasztása", list(ceg_dict.keys()))
        with st.form("kontakto_form"):
            fn = st.text_input("Keresztnév")
            ln = st.text_input("Vezetéknév")
            em = st.text_input("Email")
            ro = st.text_input("Pozíció")
            if st.form_submit_button("Kapcsolattartó mentése"):
                insert_contact(ceg_dict[selected], fn, ln, em, ro)
                st.rerun()
