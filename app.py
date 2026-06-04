import streamlit as st
import pandas as pd
import datetime
import db

st.set_page_config(page_title="Optitex Pro ERP", layout="wide")

# Egyedi CSS a Grist-szerű letisztult, modern kártyákhoz és nyomtatási nézethez
st.markdown("""
    <style>
    .customer-card { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #4A90E2; margin-bottom: 15px; }
    .print-box { background-color: white; border: 1px solid #ddd; padding: 40px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; }
    @media print {
        body * { visibility: hidden; }
        .print-area, .print-area * { visibility: visible; }
        .print-area { position: absolute; left: 0; top: 0; width: 100%; }
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("🧵 Optitex ERP v3.0")
menu = st.sidebar.radio("Navigáció", [
    "🏠 Kezdőlap & Ügyfél Dashboard", 
    "➕ Új Ügyfél / Kontakt", 
    "🚀 Új Projekt indítása",
    "📐 Új Szabásminta / Ajánlat",
    "🧾 Elszámolások (Komplex Kezelő)"
])

companies = db.get_companies()
comp_dict = {c['company_name']: c['id'] for c in companies} if companies else {}

# ==========================================
# 1. KEZDŐLAP & ÜGYFÉL DASHBOARD (Formázott 360° nézet)
# ==========================================
if menu == "🏠 Kezdőlap & Ügyfél Dashboard":
    st.title("🏠 Ügyfél-központú Vezérlőpult")
    
    if companies:
        selected_name = st.selectbox("Válassz ügyfelet a gyorsjelentés megtekintéséhez:", list(comp_dict.keys()))
        c = next(item for item in companies if item['company_name'] == selected_name)
        
        # Formázott céginfó kártya alul-felül elrendezésben
        st.markdown(f"""
        <div class="customer-card">
            <h2>🏢 {c['company_name']}</h2>
            <p><b>Székhely:</b> {c.get('address') or 'Nincs megadva'} | <b>Adószám:</b> {c.get('tax_number') or 'Nincs megadva'}</p>
            <p><b>Iparág:</b> {c.get('industry', 'Általános')} | <b>Státusz:</b> {c.get('status', 'aktív')} | <b>Ügyfél besorolás:</b> {c.get('client_value', 'C')}-kategória</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Pénzügyi és projekt gyors-mérőszámok (Metrics)
        projs = db.get_projects_by_company(c['id'])
        settles = db.get_settlements_by_company(c['id'])
        
        active_p_count = len([p for p in projs if p['status'] not in ['kész', 'lezárva', 'stornó']]) if projs else 0
        total_settled_net = sum([s['net_huf'] for s in settles]) if settles else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Futó aktív projektek", f"{active_p_count} db")
        col2.metric("Eddigi elszámolt nettó összeg", f"{total_settled_net:,} Ft")
        col3.metric("Fizetési fegyelem", c.get('payment_discipline', 'Jó / Normál'))
        
        # Gyorsfülek az összes kapcsolódó adathoz
        st.write("### 📊 Minden adat az ügyfélről")
        t_proj, t_patt, t_sett = st.tabs(["📂 Gyártási Projektek", "✂️ Szabásminták (Modellek)", "🧾 Összes Elszámolás"])
        
        with t_proj:
            if projs: st.dataframe(pd.DataFrame(projs)[['project_number', 'project_name', 'type', 'status', 'priority', 'fee_net_huf']], use_container_width=True)
            else: st.info("Nincsenek projektek.")
        with t_patt:
            patts = db.get_patterns_by_company(c['id'])
            if patts: st.dataframe(pd.DataFrame(patts)[['item_number', 'model_name', 'category', 'gender', 'version', 'status']], use_container_width=True)
            else: st.info("Nincsenek szabásminták.")
        with t_sett:
            if settles: st.dataframe(pd.DataFrame(settles)[['settlement_number', 'settlement_name', 'period_from', 'period_to', 'net_huf', 'status']], use_container_width=True)
            else: st.info("Nincsenek elszámolások.")
            
    else:
        st.info("Üdvözöllek az Optitex ERP-ben! Kezdésként vegyél fel egy új ügyfelet a bal oldali menüben.")

# ==========================================
# 5. ELSZÁMOLÁSOK (Komplex Kezelő: Látás, Módosítás, Törlés, Nyomtatás)
# ==========================================
elif menu == "🧾 Elszámolások kezelése":
    st.title("🧾 Komplex Elszámolás-kezelő Központ")
    
    if companies:
        selected_comp_name = st.selectbox("Válassz ügyfelet az elszámolások kezeléséhez:", list(comp_dict.keys()))
        active_company_id = comp_dict[selected_comp_name]
        
        # Két fő részre bontjuk: Kezelés/Nyomtatás és Új felvitele
        action_mode = st.radio("Mit szeretnél tenni?", ["📂 Meglévő elszámolások megtekintése, módosítása, nyomtatása", "➕ Új elszámolás/tétel felvitele"], horizontal=True)
        
        if action_mode == "📂 Meglévő elszámolások megtekintése, módosítása, nyomtatása":
            settles = db.get_settlements_by_company(active_company_id)
            
            if settles:
                df_set = pd.DataFrame(settles)
                st.write("### 1. Elszámolási Fejlécek (Grist-szerűen szerkeszthető!)")
                st.caption("💡 Tipp: A táblázat celláiba kattintva közvetlenül módosíthatod a nevet, időszakot vagy megjegyzést, majd nyomd meg a Mentés gombot!")
                
                # Excel/Grist szerű élő szerkesztő a fejlécekre
                edited_set_df = st.data_editor(
                    df_set[['id', 'settlement_number', 'settlement_name', 'period_from', 'period_to', 'invoice_number', 'note', 'status']],
                    key="set_editor",
                    num_rows="dynamic",
                    use_container_width=True,
                    disabled=["settlement_number"]
                )
                
                # Fejléc módosítások és törlések lekezelése
                if st.button("Fejlécek változásainak mentése / Törlések végrehajtása"):
                    # Ellenőrizzük, hogy töröltek-e sort
                    current_ids = edited_set_df['id'].tolist()
                    for original_row in settles:
                        if original_row['id'] not in current_ids:
                            db.delete_settlement(original_row['id'])
                            st.success(f"Elszámolás törölve!")
                    
                    # Frissítések mentése
                    for _, row in edited_set_df.iterrows():
                        db.update_settlement(row['id'], {
                            "settlement_name": row['settlement_name'],
                            "period_from": str(row['period_from']),
                            "period_to": str(row['period_to']),
                            "invoice_number": row['invoice_number'],
                            "note": row['note'],
                            "status": row['status']
                        })
                    st.success("Minden módosítás sikeresen mentve a Supabase adatbázisba!")
                    st.rerun()

                st.write("---")
                
                # Kiválasztunk EGY konkrét elszámolást a tételek kibontásához és nyomtatásához
                sel_set_num = st.selectbox("Válassz ki egy Elszámolást a tételek megtekintéséhez és NYOMTATÁSÁHOZ:", df_set['settlement_number'].unique())
                active_set_row = df_set[df_set['settlement_number'] == sel_set_num].iloc[0]
                
                # Lekérjük a konkrét elszámolás tételeit
                items = db.get_settlement_items(active_set_row['id'])
                
                if items:
                    df_items = pd.DataFrame(items)
                    st.write(f"### 📝 A(z) {sel_set_num} elszámoláshoz tartozó tételek listája")
                    
                    # Excel-szerű szerkesztő a tételekhez (Mennyiség, Egységár, Név módosítható, vagy akár törölhető)
                    edited_items_df = st.data_editor(
                        df_items[['id', 'item_name', 'service_type', 'quantity', 'unit', 'unit_price_net_huf', 'work_done']],
                        key="items_editor",
                        num_rows="dynamic",
                        use_container_width=True
                    )
                    
                    if st.button("Tételek változásainak mentése / Sorok törlése"):
                        # Törlések kezelése
                        item_current_ids = edited_items_df['id'].tolist()
                        for orig_item in items:
                            if orig_item['id'] not in item_current_ids:
                                db.delete_settlement_item(orig_item['id'])
                        
                        # Frissítések kezelése
                        for _, r in edited_items_df.iterrows():
                            total_calc = int(float(r['quantity']) * int(r['unit_price_net_huf']))
                            db.update_settlement_item(r['id'], {
                                "item_name": r['item_name'],
                                "service_type": r['service_type'],
                                "quantity": float(r['quantity']),
                                "unit": r['unit'],
                                "unit_price_net_huf": int(r['unit_price_net_huf']),
                                "total_net_huf": total_calc,
                                "work_done": r['work_done']
                            })
                        
                        # Újraolvassuk a tételeket és frissítjük a fejléc összegét is automatikusan!
                        updated_items = db.get_settlement_items(active_set_row['id'])
                        new_net_total = sum([ui['total_net_huf'] for ui in updated_items])
                        db.update_settlement(active_set_row['id'], {"net_huf": new_net_total, "gross_huf": int(new_net_total * 1.27)})
                        
                        st.success("Tételek sikeresen frissítve és az elszámolás végösszege újraszámolva!")
                        st.rerun()
                        
                    # ==========================================
                    # NYOMTATÁSI KÉP GENERÁLÁSA (Fejléc + Tételek egyben)
                    # ==========================================
                    st.write("---")
                    st.write("### 🖨️ Nyomtatható verzió generálása")
                    
                    if st.checkbox("Nyomtatási kép megjelenítése"):
                        st.markdown("<div class='print-area print-box'>", unsafe_allow_html=True)
                        st.write(f"## ELSZÁMOLÁSI JEGYZŐKÖNYV: {active_set_row['settlement_number'] or ''}")
                        st.write(f"**Kiállító:** Optitex Modellezés és Szabásminta Stúdió")
                        st.write(f"**Ügyfél:** {selected_comp_name}")
                        st.write(f"**Elszámolási időszak:** {active_set_row['period_from']} - {active_set_row['period_to']}")
                        st.write(f"**Státusz:** {active_set_row['status'].upper()}")
                        st.write("-----------------------------------------------------------------------------------------")
                        st.write(f"### RÉSZLETES ELVÉGZETT MUNKÁK (TÉTELEK):")
                        
                        # Szépen formázott nyomdai szöveges táblázat készítése
                        for idx, item in enumerate(items, 1):
                            st.write(f"{idx}. {item['item_name']} ({item['service_type']})")
                            st.write(f"   Mennyiség: {item['quantity']} {item['unit']} | Egységár: {item['unit_price_net_huf']:,} Ft | Nettó érték: {item['total_net_huf']:,} Ft")
                            if item.get('work_done'): st.write(f"   *Leírás: {item['work_done']}*")
                            st.write("-" * 50)
                            
                        st.write("-----------------------------------------------------------------------------------------")
                        st.write(f"## ÖSSZESÍTŐ NETTÓ VÉGÖSSZEG: {active_set_row['net_huf']:,} Ft")
                        st.write(f"Számított Bruttó Érték (27% ÁFA): {int(active_set_row['net_huf'] * 1.27):,} Ft")
                        if active_set_row.get('note'): st.write(f"**Megjegyzés:** {active_set_row['note']}")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        st.button("🖨️ Nyomtatás indítása (Ctrl + P / Cmd + P)", on_click=st.write, args=("Tipp: Használd a böngésződ beépített nyomtatás/PDF-be mentés funkcióját!",))

                else:
                    st.info("Ehhez az elszámoláshoz még nincsenek felvéve tételek.")
            else:
                st.info("Ehhez az ügyfélhez még egyetlen elszámolás sincs nyitva.")
                
        elif action_mode == "➕ Új elszámolás/tétel felvitele":
            # (Ide került a korábbi tiszta rögzítő felületed változatlanul)
            t1, t2 = st.tabs(["📑 Új Elszámolási Fejléc Nyitása", "📝 Új Tétel Hozzáadása"])
            with t1:
                with st.form("form_new_set"):
                    s_name = st.text_input("Elszámolás megnevezése *")
                    is_legacy = st.checkbox("Ez egy régi, rendszeren kívüli követetlen munka")
                    col1, col2 = st.columns(2)
                    p_from = col1.date_input("Időszak eleje", datetime.date(2024,1,1))
                    p_to = col2.date_input("Időszak vége", datetime.date.today())
                    if st.form_submit_button("Mentés"):
                        if s_name:
                            existing_count = len(db.get_settlements_by_company(active_company_id))
                            s_num = f"ELSZ-2026-{str(existing_count + 1).zfill(3)}"
                            db.insert_settlement({"company_id": active_company_id, "settlement_number": s_num, "settlement_name": s_name, "period_from": str(p_from), "period_to": str(p_to), "status": "piszkozat"})
                            st.success(f"Fejléc nyitva: {s_num}")
                            st.rerun()
            with t2:
                settles = db.get_settlements_by_company(active_company_id)
                if settles:
                    s_dict = {f"{s['settlement_number']} - {s['settlement_name']}": s['id'] for s in settles}
                    sel_s = st.selectbox("Melyik elszámoláshoz adod?", list(s_dict.keys()))
                    with st.form("form_new_item"):
                        i_name = st.text_input("Tétel neve / Elvégzett munka *")
                        s_type = st.selectbox("Típus", ["szerkesztés", "szériázás", "grading", "modellezés", "marker", "egyéb"])
                        col1, col2 = st.columns(2)
                        qty = col1.number_input("Mennyiség", value=1.0)
                        price = col2.number_input("Nettó egységár (Ft)", value=10000, step=1000)
                        work_done = st.text_area("Részletes leírás")
                        if st.form_submit_button("Tétel hozzáadása"):
                            if i_name:
                                total_calc = int(qty * price)
                                db.insert_settlement_item({"settlement_id": s_dict[sel_s], "item_name": i_name, "service_type": s_type, "quantity": float(qty), "unit_price_net_huf": int(price), "total_net_huf": total_calc, "work_done": work_done})
                                
                                # Frissítjük a fejléc végösszegét is az adatbázisban
                                updated_items = db.get_settlement_items(s_dict[sel_s])
                                new_net_total = sum([ui['total_net_huf'] for ui in updated_items])
                                db.update_settlement(s_dict[sel_s], {"net_huf": new_net_total, "gross_huf": int(new_net_total * 1.27)})
                                st.success("Tétel rögzítve és elszámolás összege frissítve!")
                else:
                    st.info("Előbb hozz létre egy fejlécet.")

# (A többi meglévő menüpont "Új Ügyfél", "Új Projekt" stb. változatlan formában megy tovább az app.py alján)
elif menu == "➕ Új Ügyfél / Kontakt":
    # Korábbi tiszta kódod változatlanul...
    pass
