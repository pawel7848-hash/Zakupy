
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dom", layout="centered")
st.markdown("<style>.block-container {padding-top: 3.5rem !important;}</style>", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "Menu Dom"
if 'sub_page' not in st.session_state:
    st.session_state.sub_page = None
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def get_data(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name)
        data.columns = data.columns.str.strip()
        return data
    except: return pd.DataFrame()

def refresh_all():
    st.cache_data.clear()
    st.rerun()

df_spizarnia = get_data("Spizarnia")
df_dania = get_data("Dania")
df_plan = get_data("Plan")
df_inne = get_data("Inne")

def kafelek_terminu(label, kategoria, nazwa_klucza):
    global df_inne
    row = df_inne[(df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)]
    today = datetime.now().date()
    data_final = today
    kolor = "gray"
    if not row.empty:
        val = str(row.iloc[0]['Wartosc']).strip()
        try: data_final = datetime.strptime(val[:10], '%Y-%m-%d').date()
        except:
            try: data_final = datetime.strptime(val[:10], '%d.%m.%Y').date()
            except: data_final = today
        kolor = "green" if data_final >= today else "red"
    with st.popover(f":{kolor}[{label}: {data_final.strftime('%d.%m.%Y')}]", use_container_width=True):
        st.write(f"Zmień datę: {label}")
        nowa = st.date_input("Data", value=data_final, format="DD.MM.YYYY", key=f"d_{kategoria}{nazwa_klucza}")
        if st.button("Zapisz", key=f"b{kategoria}_{nazwa_klucza}"):
            nowa_str = nowa.strftime('%Y-%m-%d')
            mask = (df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)
            if not df_inne[mask].empty: df_inne.loc[mask, 'Wartosc'] = nowa_str
            else:
                new_r = pd.DataFrame([{"Kategoria": kategoria, "Nazwa": nazwa_klucza, "Wartosc": nowa_str}])
                df_inne = pd.concat([df_inne, new_r], ignore_index=True)
            conn.update(worksheet="Inne", data=df_inne)
            refresh_all()

if st.session_state.page == "Menu Dom":
    st.title("🏠 MENU GŁÓWNE")
    st.divider()
    if st.button("🍳 KUCHNIA", use_container_width=True): st.session_state.page = "Kuchnia"; st.rerun()
    if st.button("🐶 PIES", use_container_width=True): st.session_state.page = "Pies"; st.rerun()
    if st.button("🚗 AUTO", use_container_width=True): st.session_state.page = "Auto"; st.rerun()

elif st.session_state.page == "Kuchnia":
    if st.button("⬅️ POWRÓT DO DOMU", use_container_width=True):
        st.session_state.page = "Menu Dom"; st.session_state.sub_page = None; st.rerun()
    if st.session_state.sub_page is None:
        st.title("🍳 KUCHNIA")
        if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): st.session_state.sub_page = "Lista"; st.rerun()
        if st.button("📦 STAN SPIŻARNI", use_container_width=True): st.session_state.sub_page = "Spizarnia"; st.rerun()
        if st.button("🥘 PRZEPISY", use_container_width=True): st.session_state.sub_page = "Dania"; st.rerun()
        if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): st.session_state.sub_page = "Plan"; st.rerun()
    elif st.session_state.sub_page == "Lista":
        if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("🛒 LISTA ZAKUPÓW")
        with st.expander("➕ DODAJ PRODUKT", expanded=False):
            with st.form("q_add_list"):
                # --- TUTAJ ZMIANA: LISTA PRODUKTÓW DO WYBORU ---
                lista_wszystkich = sorted(df_spizarnia['Produkt'].unique().tolist()) if not df_spizarnia.empty else []
                q_n = st.selectbox("Wybierz produkt (możesz wpisać nazwę):", [""] + lista_wszystkich, help="Zacznij pisać, aby przefiltrować listę")
                # Jeśli produktu nie ma na liście, używamy pola niżej:
                new_p_name = st.text_input("LUB wpisz zupełnie nowy produkt (jeśli nie ma go wyżej):")

                ist_m = sorted(df_spizarnia['Miejsce'].unique()) if not df_spizarnia.empty else []
                c1, c2 = st.columns(2)
                with c1: wyb = st.selectbox("Miejsce:", ["+ NOWE"] + ist_m)
                with c2: n_m = st.text_input("Lub wpisz nowe miejsce:")

                if st.form_submit_button("DODAJ DO LISTY", use_container_width=True):
                    # Decydujemy, którą nazwę wziąć: z listy czy z pola tekstowego
                    final_name = new_p_name if new_p_name else q_n

                    if final_name:
                        f_m = n_m if n_m else (wyb if wyb != "+ NOWE" else "Inne")
                        df_spizarnia = df_spizarnia.dropna(subset=['Produkt'])
                        mask = df_spizarnia['Produkt'].str.lower() == final_name.lower()

                        if not df_spizarnia[mask].empty:
                            df_spizarnia.loc[mask, 'Stan'] = "Brak"
                            df_spizarnia.loc[mask, 'Miejsce'] = f_m
                        else:
                            nw = pd.DataFrame([{"Produkt": final_name, "Stan": "Brak", "Miejsce": f_m}])
                            df_spizarnia = pd.concat([df_spizarnia, nw], ignore_index=True)

                        conn.update(worksheet="Spizarnia", data=df_spizarnia)
                        refresh_all()
        st.divider()
        braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
        for idx, r in braki.iterrows():
            if st.button(f"🔴 {r['Produkt']} ({r['Miejsce']})", key=f"l_{idx}", use_container_width=True):
                df_spizarnia.at[idx, 'Stan'] = "Mamy"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
    elif st.session_state.sub_page == "Spizarnia":
        if st.session_state.wybrane_miejsce is None:
            if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
            miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
            for m in miejsca:
                if st.button(f"📂 {m.upper()}", use_container_width=True): st.session_state.wybrane_miejsce = m; st.rerun()
        else:
            if st.button("⬅️ POWRÓT", use_container_width=True): st.session_state.wybrane_miejsce = None; st.rerun()
            m = st.session_state.wybrane_miejsce
            st.subheader(f"Lokalizacja: {m}")
            for idx, r in df_spizarnia[df_spizarnia['Miejsce'] == m].iterrows():
                stan = r['Stan']
                ikona = "🟢" if stan == "Mamy" else ("🟡" if stan == "Sprawdź" else "🔴")
                c1, c2 = st.columns([2, 1])
                c1.write(f"{ikona} {r['Produkt']}")
                with c2.popover("Zmień stan"):
                    if st.button("🟢 MAMY", key=f"m_{idx}", use_container_width=True):
                        df_spizarnia.at[idx, 'Stan'] = "Mamy"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
                    if st.button("🟡 SPRAWDŹ", key=f"s_{idx}", use_container_width=True):
                        df_spizarnia.at[idx, 'Stan'] = "Sprawdź"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
                    if st.button("🔴 BRAK", key=f"b_{idx}", use_container_width=True):
                        df_spizarnia.at[idx, 'Stan'] = "Brak"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
    elif st.session_state.sub_page == "Dania":
        if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()

        with st.expander("➕ DODAJ NOWY PRZEPIS"):
            with st.form("a_d"):
                dn = st.text_input("Nazwa dania:")
                ds = st.text_area("Składniki (rozdzielaj przecinkami):")
                if st.form_submit_button("ZAPISZ NOWE DANIE", use_container_width=True):
                    if dn:
                        nw = pd.DataFrame([{"Nazwa": dn, "Skladniki": ds}])
                        df_dania = pd.concat([df_dania, nw], ignore_index=True)
                        conn.update(worksheet="Dania", data=df_dania); refresh_all()

        st.divider()
        df_clean = df_dania.dropna(subset=['Nazwa']) if not df_dania.empty else pd.DataFrame()

        for idx, d in df_clean.iterrows():
            n_str = str(d['Nazwa'])
            s_str = str(d['Skladniki']) if pd.notnull(d['Skladniki']) else ""

            with st.expander(f"🍴 {n_str.upper()}"):
                st.write(f"Składniki: {s_str}")
                c1, c2 = st.columns(2)
                if c1.button("🗑️ USUŃ", key=f"del_d_{idx}", use_container_width=True):
                    df_dania = df_dania.drop(idx)
                    conn.update(worksheet="Dania", data=df_dania); refresh_all()
                with c2.popover("📝 EDYTUJ SKŁADNIKI", use_container_width=True):
                    new_s = st.text_area("Popraw składniki:", value=s_str, key=f"ed_s_{idx}")
                    if st.button("ZAPISZ ZMIANY", key=f"sav_d_{idx}"):
                        df_dania.at[idx, 'Skladniki'] = new_s
                        conn.update(worksheet="Dania", data=df_dania); refresh_all()

    elif st.session_state.sub_page == "Plan":
        if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("📅 PLAN POSIŁKÓW")
        dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        with st.expander("➕ DODAJ DANIE DO PLANU"):
            with st.form("f_plan_nowy"):
                d_wybor = st.selectbox("Wybierz dzień:", dni)
                lista_dan = df_dania['Nazwa'].dropna().unique().tolist() if not df_dania.empty else []
                danie_wybor = st.selectbox("Wybierz danie:", lista_dan if lista_dan else ["Brak dań"])
                if st.form_submit_button("DODAJ DO PLANU", use_container_width=True):
                    if danie_wybor != "Brak dań":
                        nw_p = pd.DataFrame([{"Dzien": d_wybor, "Danie": danie_wybor}])
                        df_plan = pd.concat([df_plan, nw_p], ignore_index=True)
                        conn.update(worksheet="Plan", data=df_plan)
                        przepis = df_dania[df_dania['Nazwa'] == danie_wybor].iloc[0]
                        skladniki = [s.strip() for s in str(przepis['Skladniki']).split(',') if s.strip()]
                        for s in skladniki:
                            mask = df_spizarnia['Produkt'].str.lower() == s.lower()
                            if not df_spizarnia[mask].empty:
                                if df_spizarnia.loc[mask, 'Stan'].values[0] != "Mamy":
                                    df_spizarnia.loc[mask, 'Stan'] = "Brak"
                            else:
                                ns = pd.DataFrame([{"Produkt": s, "Stan": "Brak", "Miejsce": "Inne"}])
                                df_spizarnia = pd.concat([df_spizarnia, ns], ignore_index=True)
                        conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
        st.divider()
        for d in dni:
            plan_dnia = df_plan[df_plan['Dzien'] == d]
            if not plan_dnia.empty:
                st.subheader(f"📅 {d}")
                for idx, p in plan_dnia.iterrows():
                    danie_nazwa = p['Danie']
                    czy_mamy = True; braki = []
                    if danie_nazwa in df_dania['Nazwa'].values:
                        przepis = df_dania[df_dania['Nazwa'] == danie_nazwa].iloc[0]
                        skladniki_d = [s.strip() for s in str(przepis['Skladniki']).split(',') if s.strip()]
                        for s in skladniki_d:
                            m = (df_spizarnia['Produkt'].str.lower() == s.lower()) & (df_spizarnia['Stan'] == "Mamy")
                            if df_spizarnia[m].empty:
                                czy_mamy = False; braki.append(s)
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if czy_mamy: st.success(f"🟢 {danie_nazwa}")
                        else: st.error(f"🔴 {danie_nazwa} (Braki: {', '.join(braki)})")
                    if col2.button("❌", key=f"del_p_{idx}"):
                        if danie_nazwa in df_dania['Nazwa'].values:
                            przepis = df_dania[df_dania['Nazwa'] == danie_nazwa].iloc[0]
                            skladniki_do_spr = [s.strip() for s in str(przepis['Skladniki']).split(',') if s.strip()]
                            for s in skladniki_do_spr:
                                mask_s = df_spizarnia['Produkt'].str.lower() == s.lower()
                                if not df_spizarnia[mask_s].empty:
                                    if df_spizarnia.loc[mask_s, 'Stan'].values[0] == "Mamy":
                                        df_spizarnia.loc[mask_s, 'Stan'] = "Sprawdź"
                            conn.update(worksheet="Spizarnia", data=df_spizarnia)
                        df_plan = df_plan.drop(idx); conn.update(worksheet="Plan", data=df_plan); refresh_all()

elif st.session_state.page == "Pies":
    if st.button("⬅️ POWRÓT", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    kafelek_terminu("💉 Szczepienie", "Pies", "Szczepienie")

elif st.session_state.page == "Auto":
    if st.button("⬅️ POWRÓT", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    kafelek_terminu("🛠️ Przegląd", "Auto", "Przegląd")
    kafelek_terminu("📄 OC", "Auto", "Ubezpieczenie")
