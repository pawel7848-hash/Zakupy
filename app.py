import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Zarządzanie Domem", layout="centered")

# Inicjalizacja stanów sesji
if 'page' not in st.session_state:
    st.session_state.page = "Menu Dom"
if 'sub_page' not in st.session_state:
    st.session_state.sub_page = None
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def get_data(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name)
        data.columns = data.columns.str.strip()
        return data
    except:
        return pd.DataFrame()

def refresh_all():
    st.cache_data.clear()
    st.rerun()

# POBIERANIE DANYCH
df_spizarnia = get_data("Spizarnia")
df_dania = get_data("Dania")
df_plan = get_data("Plan")

# Funkcje nawigacji
def wejdz_do_kuchni():
    st.session_state.page = "Kuchnia"
    st.rerun()

def wroc_do_domu():
    st.session_state.page = "Menu Dom"
    st.session_state.sub_page = None
    st.rerun()

def zmien_sekcje_kuchni(nazwa):
    st.session_state.sub_page = nazwa
    st.session_state.wybrane_miejsce = None
    st.rerun()

# =========================================================
# --- EKRAN STARTOWY: DOM ---
# =========================================================
if st.session_state.page == "Menu Dom":
    st.title("🏠 DOM")
    st.divider()
    
    # Główna kategoria
    if st.button("🍳 KUCHNIA", use_container_width=True):
        wejdz_do_kuchni()
    
    # Tutaj w przyszłości możesz dodać:
    # if st.button("🚗 GARAŻ", use_container_width=True): pass
    # if st.button("🧹 PORZĄDKI", use_container_width=True): pass

# =========================================================
# --- KATEGORIA: KUCHNIA ---
# =========================================================
elif st.session_state.page == "Kuchnia":
    
    # Widok wyboru funkcji wewnątrz kuchni
    if st.session_state.sub_page is None:
        if st.button("⬅️ WRÓĆ DO MENU DOM", use_container_width=True):
            wroc_do_domu()
        
        st.title("🍳 KUCHNIA")
        st.divider()
        if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): zmien_sekcje_kuchni("Lista")
        if st.button("📦 STAN SPIŻARNI", use_container_width=True): zmien_sekcje_kuchni("Spizarnia")
        if st.button("🥘 PRZEPISY (DANIA)", use_container_width=True): zmien_sekcje_kuchni("Dania")
        if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): zmien_sekcje_kuchni("Plan")

    # --- PODSTRONA: LISTA ZAKUPÓW ---
    elif st.session_state.sub_page == "Lista":
        if st.button("⬅️ WRÓĆ DO KUCHNI", use_container_width=True): zmien_sekcje_kuchni(None)
        st.title("🛒 DO KUPIENIA")
        braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
        for index, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']} ({row.get('Miejsce', 'Brak')})", key=f"k_{index}_{row['Produkt']}", use_container_width=True):
                df_spizarnia.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                refresh_all()

    # --- PODSTRONA: STAN SPIŻARNI ---
    elif st.session_state.sub_page == "Spizarnia":
        if st.session_state.wybrane_miejsce is None:
            if st.button("⬅️ WRÓĆ DO KUCHNI", use_container_width=True): zmien_sekcje_kuchni(None)
            st.title("📦 WYBIERZ MIEJSCE")
            miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
            for m in miejsca:
                if st.button(f"📂 {m.upper()}", key=f"m_{m}", use_container_width=True):
                    st.session_state.wybrane_miejsce = m
                    st.rerun()
        else:
            col1, col2 = st.columns(2)
            col1.button("⬅️ MIEJSCA", on_click=lambda: st.session_state.update({"wybrane_miejsce": None}), use_container_width=True)
            col2.button("🏠 KUCHNIA", on_click=lambda: zmien_sekcje_kuchni(None), use_container_width=True)
            
            miejsce = st.session_state.wybrane_miejsce
            st.header(f"📍 {miejsce.upper()}")
            with st.expander("➕ Dodaj produkt"):
                with st.form("q_add", clear_on_submit=True):
                    nowy = st.text_input("Nazwa:")
                    if st.form_submit_button("Zapisz"):
                        if nowy:
                            new_r = pd.DataFrame([{"Produkt": nowy, "Stan": "Mamy", "Miejsce": miejsce}])
                            df_upd = pd.concat([df_spizarnia, new_r], ignore_index=True)
                            conn.update(worksheet="Spizarnia", data=df_upd)
                            refresh_all()
            st.divider()
            produkty = df_spizarnia[df_spizarnia['Miejsce'] == miejsce]
            for index, row in produkty.iterrows():
                ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
                if st.button(f"{ikona} {row['Produkt']}", key=f"s_{index}_{row['Produkt']}", use_container_width=True):
                    df_spizarnia.at[index, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                    conn.update(worksheet="Spizarnia", data=df_spizarnia)
                    refresh_all()

    # --- PODSTRONA: PRZEPISY ---
    elif st.session_state.sub_page == "Dania":
        if st.button("⬅️ WRÓĆ DO KUCHNI", use_container_width=True): zmien_sekcje_kuchni(None)
        st.title("🥘 PRZEPISY")
        t1, t2 = st.tabs(["Twoje Dania", "Dodaj Przepis"])
        with t2:
            with st.form("f_dania"):
                n_d = st.text_input("Nazwa:")
                sk = st.text_area("Składniki (po przecinku):")
                if st.form_submit_button("Zapisz"):
                    new_d = pd.DataFrame([{"Nazwa": n_d, "Skladniki": sk}])
                    df_upd = pd.concat([df_dania, new_d], ignore_index=True)
                    conn.update(worksheet="Dania", data=df_upd)
                    refresh_all()
        with t1:
            for idx, d in df_dania.iterrows():
                with st.expander(f"🍴 {str(d['Nazwa']).upper()}"):
                    st.write(d['Skladniki'])

    # --- PODSTRONA: PLAN POSIŁKÓW ---
    elif st.session_state.sub_page == "Plan":
        if st.button("⬅️ WRÓĆ DO KUCHNI", use_container_width=True): zmien_sekcje_kuchni(None)
        st.title("📅 PLAN TYGODNIOWY")
        dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        
        with st.expander("➕ DODAJ POSIŁEK"):
            with st.form("f_p"):
                wybr_d = st.selectbox("Dzień:", dni)
                wybr_n = st.selectbox("Danie:", df_dania['Nazwa'].unique()) if not df_dania.empty else st.selectbox("Danie:", ["Brak dań"])
                if st.form_submit_button("Dodaj"):
                    new_p = pd.DataFrame([{"Dzien": wybr_d, "Danie": wybr_n}])
                    df_plan = pd.concat([df_plan, new_p], ignore_index=True)
                    conn.update(worksheet="Plan", data=df_plan)
                    # Sprawdzanie braków
                    p_info = df_dania[df_dania['Nazwa'] == wybr_n].iloc[0]
                    skł = [s.strip() for s in str(p_info['Skladniki']).split(',')]
                    for s in skł:
                        match = df_spizarnia[df_spizarnia['Produkt'].str.contains(s, case=False, na=False)]
                        if match.empty:
                            new_row = pd.DataFrame([{"Produkt": s, "Stan": "Brak", "Miejsce": "Inne"}])
                            df_spizarnia = pd.concat([df_spizarnia, new_row], ignore_index=True)
                        elif (match['Stan'] != "Mamy").all():
                            df_spizarnia.loc[df_spizarnia['Produkt'].str.contains(s, case=False, na=False), 'Stan'] = "Brak"
                    conn.update(worksheet="Spizarnia", data=df_spizarnia)
                    refresh_all()

        st.divider()
        for d in dni:
            p_dnia = df_plan[df_plan['Dzien'] == d]
            if not p_dnia.empty:
                st.subheader(f"🗓️ {d}")
                for idx, p in p_dnia.iterrows():
                    # Logika kropki
                    d_info = df_dania[df_dania['Nazwa'] == p['Danie']]
                    kropka = "⚪"
                    if not d_info.empty:
                        skł = [s.strip() for s in str(d_info.iloc[0]['Skladniki']).split(',')]
                        komplet = True
                        for s in skł:
                            if df_spizarnia[(df_spizarnia['Produkt'].str.contains(s, case=False, na=False)) & (df_spizarnia['Stan'] == "Mamy")].empty:
                                komplet = False; break
                        kropka = "🟢" if komplet else "🔴"
                    
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"{kropka} {p['Danie']}")
                    if c2.button("❌", key=f"del_{idx}"):
                        df_plan = df_plan.drop(idx)
                        conn.update(worksheet="Plan", data=df_plan)
                        refresh_all()

