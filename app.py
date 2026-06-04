import streamlit as st
import pandas as pd
import datetime
import db

st.set_page_config(page_title="Optitex Textil ERP", layout="wide")

st.sidebar.title("🧵 Optitex ERP v2.5")
menu = st.sidebar.radio("Funkciók", [
    "🏢 Ügyfélközpont", 
    "➕ Új Ügyfél / Kontakt", 
    "🚀 Új Projekt indítása",
    "📐 Új Szabásminta / Ajánlat",
    "🧾 Elszámolások kezelése"
])

# ==========================================
# 1. ÜGYFÉLKÖZPONT (Minden adat egy helyen)
# ==========================================
if menu == "🏢 Ügyfélközpont":
    st.title("🏢 Központi Ügyféladatbázis és Életút")
    companies = db.get_companies()
    
    if companies:
        df_comp = pd.DataFrame(companies)
        selected_name = st.selectbox("Válassz ki egy ügyfelet a részletes adatok megtekintéséhez:", df_comp['company_name'].unique())
        c = next(item for item in companies if item['company_name'] == selected_name)
        
        # Cég gyors-statisztika
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Státusz", c.get('status', 'aktív'))
        col2.metric("Ügyfél értéke", c.get('client_value', 'C'))
        col3.write(f"**Adószám:** {c.get('tax_number') or 'Nincs'}")
        col3.write(f"**Székhely:** {c.get('address') or 'Nincs'}")
        col4.write(f"**Fizetési feltétel:** {c.get('payment_term') or 'Azonnali'}")
        col4.write(f"**ÁFA státusz:** {c.get('vat_status') or 'belföldi'}")
        
        st.write("---")
        
        tab_contact, tab_proj, tab_patt, tab_quote, tab_settle = st.tabs([
            "👤 Kapcsolattartók", "📂 Gyártási Projektek", "✂️ Szabásminták", "📄 Árajánlatok", "🧾 Elszámolások története"
        ])
        
        with tab_contact:
            contacts = db.get_contacts_by_company(c['id'])
            if contacts:
                st.dataframe(pd.DataFrame(contacts).drop(columns=['id', 'company_id']), use_container_width=True)
            else:
                st.info("Nincs rögzített kapcsolattartó.")
                
        with tab_proj:
            projects = db.get_projects_by_company(c['id'])
            if projects:
                st.dataframe(pd.DataFrame(projects).drop(columns=['id', 'company_id']), use_container_width=True)
            else:
                st.info("Nincsenek projektek.")
                
        with tab_patt:
            patterns = db.get_patterns_by_company(c['id'])
            if patterns:
                st.dataframe(pd.DataFrame(patterns).drop(columns=['id', 'company_id']), use_container_width=True)
            else:
                st.info("Nincsenek szabásminták.")
                
        with tab_quote:
            quotes = db.get_quotes_by_company(c['id'])
            if quotes:
                st.dataframe(pd.DataFrame(quotes).drop(columns=['id', 'company_id']), use_container_width=True)
            else:
                st.info("Nincsenek árajánlatok.")
                
        with tab_settle:
            settlements = db.get_settlements_by_company(c['id'])
            if settlements:
                df_set = pd.DataFrame(settlements)
                st.dataframe(df_set.drop(columns=['id', 'company_id']), use_container_width=True)
                
                st.write("### 🔍 Elszámolás részletes tételei")
                sel_set_num = st.selectbox("Válassz ki egy elszámolás-számot a tételek kibontásához:", df_set['settlement_number'].unique())
                sel_set_id = df_set[df_set['settlement_number'] == sel_set_num]['id'].values[0]
                
                items = db.get_settlement_items(sel_set_id)
                if items:
                    st.dataframe(pd.DataFrame(items).drop(columns=['id', 'settlement_id']), use_container_width=True)
                else:
                    st.info("Ehhez az elszámoláshoz még nem adtál hozzá tételeket.")
            else:
                st.info("Ehhez az ügyfélhez még nem készült elszámolás.")
    else:
        st.warning("Nincsenek adatok az adatbázisban.")

# ==========================================
# 2. ÚJ ÜGYFÉL / KONTAKT
# ==========================================
elif menu == "➕ Új Ügyfél / Kontakt":
    t1, t2 = st.tabs(["🏢 Új Cég rögzítése", "👤 Új Kapcsolattartó"])
    
    with t1:
        st.subheader("Cég adatlap")
        with st.form("form_company"):
            c_name = st.text_input("Cégnév *")
            tax = st.text_input("Adószám")
            addr = st.text_area("Cím")
            col1, col2 = st.columns(2)
            ind = col1.selectbox("Iparág", ["divat", "munkavédelem", "sport", "gyerek", "uniformis", "egyéb"])
            stat = col2.selectbox("Státusz", ["aktív", "inaktív", "prospect"])
            if st.form_submit_button("Cég mentése"):
                if c_name:
                    db.insert_company({"company_name": c_name, "tax_number": tax, "address": addr, "industry": ind, "status": stat})
                    st.success(f"'{c_name}' elmentve!")
                    st.rerun()
                else:
                    st.error("Cégnév kötelező!")

    with t2:
        st.subheader("Kapcsolattartó hozzáadása")
        companies = db.get_companies()
        if companies:
            comp_dict = {c['company_name']: c['id'] for c in companies}
            with st.form("form_contact"):
                sel_comp = st.selectbox("Cég *", list(comp_dict.keys()))
                con_name = st.text_input("Név *")
                pos = st.text_input("Beosztás")
                email = st.text_input("Email")
                mob = st.text_input("Mobil")
                if st.form_submit_button("Mentés"):
                    if con_name:
                        db.insert_contact({"company_id": comp_dict[sel_comp], "contact_name": con_name, "position": pos, "email": email, "mobile": mob})
                        st.success("Sikeres mentés!")
                    else:
                        st.error("Név kötelező!")

# ==========================================
# 3. ÚJ PROJEKT
# ==========================================
elif menu == "🚀 Új Projekt indítása":
    st.title("🚀 Új Projekt indítása")
    companies = db.get_companies()
    if companies:
        comp_dict = {c['company_name']: c['id'] for c in companies}
        with st.form("form_project"):
            sel_comp = st.selectbox("Ügyfél *", list(comp_dict.keys()))
            p_name = st.text_input("Projekt neve *")
            col1, col2 = st.columns(2)
            p_type = col1.selectbox("Típus", ["szerkesztés", "szériázás", "grading", "modellezés", "javítás", "marker", "DXF export", "kombinált", "konzultáció"])
            p_prio = col2.selectbox("Prioritás", ["🔴 sürgős", "🟡 normál", "🟢 ráér"])
            fee = st.number_input("Nettó tervezési díj (Ft)", value=0, step=5000)
            
            if st.form_submit_button("Projekt létrehozása"):
                if p_name:
                    p_num = f"PROJ-2026-{str(len(db.get_projects_by_company(comp_dict[sel_comp])) + 1).zfill(3)}"
                    db.insert_project({
                        "company_id": comp_dict[sel_comp], "project_number": p_num, "project_name": p_name,
                        "type": p_type, "priority": p_prio, "fee_net_huf": int(fee)
                    })
                    st.success(f"Projekt létrehozva: {p_num}")
                else:
                    st.error("Név kötelező!")

# ==========================================
# 4. SZABÁSMINTA / AJÁNLAT
# ==========================================
elif menu == "📐 Új Szabásminta / Ajánlat":
    t1, t2 = st.tabs(["📐 Új Szabásminta (Modell)", "💰 Árajánlat"])
    companies = db.get_companies()
    if companies:
        comp_dict = {c['company_name']: c['id'] for c in companies}
        
        with t1:
            with st.form("form_pattern"):
                sel_comp = st.selectbox("Ügyfél", list(comp_dict.keys()))
                item_num = st.text_input("Cikkszám (Pl. SZM-01)")
                m_name = st.text_input("Modell neve *")
                if st.form_submit_button("Szabásminta mentése"):
                    if m_name:
                        db.insert_pattern({"company_id": comp_dict[sel_comp], "item_number": item_num, "model_name": m_name})
                        st.success("Modell regisztrálva!")
                    else:
                        st.error("Modell név kötelező!")
                        
        with t2:
            with st.form("form_quote"):
                sel_comp = st.selectbox("Ügyfél választása", list(comp_dict.keys()))
                q_name = st.text_input("Ajánlat tárgya *")
                net_val = st.number_input("Nettó érték (Ft)", value=0)
                if st.form_submit_button("Ajánlat mentése"):
                    if q_name:
                        q_num = f"AJ-2026-{str(len(db.get_quotes_by_company(comp_dict[sel_comp])) + 1).zfill(3)}"
                        db.insert_quote({"company_id": comp_dict[sel_comp], "quote_number": q_num, "quote_name": q_name, "net_huf": int(net_val), "gross_huf": int(net_val * 1.27)})
                        st.success(f"Ajánlat rögzítve: {q_num}")

# ==========================================
# 5. ELSZÁMOLÁSOK (A rugalmas, múltat kezelő modul)
# ==========================================
elif menu == "🧾 Elszámolások kezelése":
    st.title("🧾 Elszámolások és Utólagos Korrekciók")
    companies = db.get_companies()
    
    if companies:
        comp_dict = {c['company_name']: c['id'] for c in companies}
        t1, t2 = st.tabs(["📑 1. Elszámolási Fejléc Nyitása", "📝 2. Tételek és Munkák Hozzáadása"])
        
        with t1:
            st.markdown("### Elszámolási időszak és keret meghatározása")
            with st.form("form_settlement"):
                sel_comp = st.selectbox("Melyik ügyfélnek készül? *", list(comp_dict.keys()))
                s_name = st.text_input("Elszámolás neve (Pl: '2023-2024-es mintázások utólagos rendezése') *")
                
                # Kulcsfontosságú jelölő a régi adatokhoz
                is_legacy = st.checkbox("⚠️ Ez egy RÉGI munka (Nincs hozzá mai projektszám vagy ajánlat az adatbázisban)")
                
                col1, col2 = st.columns(2)
                p_from = col1.date_input("Időszak eleje", datetime.date(2023, 1, 1))
                p_to = col2.date_input("Időszak vége", datetime.date.today())
                
                col3, col4 = st.columns(2)
                adv = col3.number_input("Levont / beszámított előleg (Ft)", min_value=0, value=0)
                inv_num = col4.text_input("Kapcsolódó kézi/régi számlaszám (ha van)")
                
                note = st.text_area("Megjegyzések az ügyfél felé")
                
                if st.form_submit_button("Elszámolási fejléc mentése"):
                    if s_name:
                        # Grist-típusú egyedi számozás generálása
                        existing_count = len(db.get_settlements_by_company(comp_dict[sel_comp]))
                        s_num = f"ELSZ-2026-{str(existing_count + 1).zfill(3)}"
                        
                        db.insert_settlement({
                            "company_id": comp_dict[sel_comp],
                            "settlement_number": s_num,
                            "settlement_name": s_name,
                            "period_from": str(p_from),
                            "period_to": str(p_to),
                            "advance_deducted_huf": int(adv),
                            "invoice_number": inv_num,
                            "note": note,
                            "status": "piszkozat"
                        })
                        st.success(f"Elszámolás elmentve! Sorszáma: {s_num}")
                    else:
                        st.error("Az Elszámolás megnevezése kötelező!")

        with t2:
            st.markdown("### Elvégzett feladatok felvitele")
            
            # Összegyűjtjük az összes létező elszámolást a tétel hozzáadáshoz
            all_settlements = []
            for c_id in comp_dict.values():
                all_settlements.extend(db.get_settlements_by_company(c_id))
                
            if all_settlements:
                settle_dict = {f"{s['settlement_number']} - {s['settlement_name']}": s for s in all_settlements}
                sel_settle_text = st.selectbox("Válassz ki egy megnyitott elszámolást:", list(settle_dict.keys()))
                
                # Kiválasztott elszámolás objektum és a hozzá tartozó cég lekérése
                active_settlement = settle_dict[sel_settle_text]
                active_company_id = active_settlement['company_id']
                
                with st.form("form_settlement_item"):
                    st.write("---")
                    st.info("💡 Amennyiben ez egy régi, követés nélküli munka, a Projekt és Szabásminta mezőket hagyd 'Nincs'-en!")
                    
                    i_name = st.text_input("Tétel / Munka megnevezése (Pl: 'Gyermek overál szériázás és marker készítés') *")
                    s_type = st.selectbox("Szolgáltatás típusa", ["szerkesztés", "szériázás", "grading", "modellezés", "javítás", "marker", "DXF export", "konzultáció", "egyéb"])
                    work_text = st.text_area("Elvégzett munka részletes leírása (Pl. adatok, amikre emlékszel)")
                    
                    # Dinamikus relációs mezők - alapértelmezetten None-ra állnak be, ha nem nyúlsz hozzájuk
                    proj_list = db.get_projects_by_company(active_company_id)
                    patt_list = db.get_patterns_by_company(active_company_id)
                    
                    p_opt = {"- Nincs / Régi követetlen munka -": None}
                    if proj_list:
                        for p in proj_list: p_opt[f"{p['project_number']} - {p['project_name']}"] = p['id']
                    sel_p = st.selectbox("Összekapcsolás mai projekttel (opcionális)", list(p_opt.keys()))
                    
                    m_opt = {"- Nincs / Régi követetlen modell -": None}
                    if patt_list:
                        for m in patt_list: m_opt[f"{m['item_number'] or ''} {m['model_name']}"] = m['id']
                    sel_m = st.selectbox("Összekapcsolás mai szabásmintával (opcionális)", list(m_opt.keys()))
                    
                    st.write("---")
                    col1, col2, col3 = st.columns(3)
                    qty = col1.number_input("Mennyiség", min_value=0.01, value=1.0)
                    unit = col2.selectbox("Egység", ["modell", "méret", "méretsor", "óra", "db"])
                    price = col3.number_input("Nettó egységár (Ft)", min_value=0, value=15000, step=1000)
                    
                    total_net = int(qty * price)
                    st.write(f"**Tétel nettó értéke:** {total_net} Ft")
                    
                    files = st.text_input("Átadott fájlok archív elérési útja / megjegyzés")
                    
                    if st.form_submit_button("Tétel hozzáadása az elszámoláshoz"):
                        if i_name:
                            db.insert_settlement_item({
                                "settlement_id": active_settlement['id'],
                                "item_name": i_name,
                                "project_id": p_opt[sel_p],
                                "pattern_id": m_opt[sel_m],
                                "service_type": s_type,
                                "work_done": work_text,
                                "quantity": float(qty),
                                "unit": unit,
                                "unit_price_net_huf": int(price),
                                "total_net_huf": total_net,
                                "delivered_files": files
                            })
                            st.success("Tétel sikeresen elmentve!")
                        else:
                            st.error("A tétel megnevezése kötelező!")
            else:
                st.info("Még nem hoztál létre elszámolási fejlécet a bal oldali fülön.")
    else:
        st.warning("Nincsenek ügyfelek az adatbázisban. Előbb hozz létre egyet az ügyfélmenüben!")
