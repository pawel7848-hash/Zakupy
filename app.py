import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Kuchnia 2.0", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = "Menu"
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def get_data(sheet_name):
    data = conn.read(worksheet=sheet_name)
    data.columns = data.columns.str.strip()
    return data

def refresh_all():
    st.cache_data.clear()
    st.rerun()

# POBIERANIE DANYCH
df_spizarnia = get_data("Spizarnia")
try:
    df_dania = get_data("Dania")
except:
    df_dania = pd.DataFrame(columns=["Nazwa", "Skladniki"])
try:
    df_plan = get_data("Plan")
except:
    df_plan = pd.DataFrame(columns=["Dzien", "Danie"])

def zmien_strone(nazwa):
    st.session_state.page = nazwa
    st.session_state.wybrane_miejsce = None
    st.rerun()

# --- MENU GŁÓWNE ---
if st.session_state.page == "Menu":
    st.title("🏠 TWOJA KUCHNIA")
    st.divider()
    if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): zmien_strone("Lista")
    if st.button("📦 STAN SPIŻARNI", use_container_width=True): zmien_strone("Spizarnia")
    if st.button("🥘 DANIA OBIADOWE", use_container_width=True): zmien_strone("Dania")
    if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): zmien_strone("Plan")

# --- SEKCJA 1: LISTA ZAKUPÓW ---
elif st.session_state.page == "Lista":
    if st.button("⬅️ POWRÓT DO MENU", use_container_width=True): zmien_strone("Menu")
    st.title("🛒 DO KUPIENIA")
    braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
    if not braki.empty:
        for index, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']} ({row.get('Miejsce', 'Brak')})", key=f"k_{index}_{row['Produkt']}", use_container_width=True):
                df_spizarnia.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                refresh_all()
    else:
        st.success("Wszystko kupione! 🎉")

# --- SEKCJA 2: STAN SPIŻARNI ---
elif st.session_state.page == "Spizarnia":
    if st.session_state.wybrane_miejsce is None:
        if st.button("🏠 MENU GŁÓWNE", use_container_width=True): zmien_strone("Menu")
        st.title("📦 WYBIERZ MIEJSCE")
        miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
        for m in miejsca:
            if st.button(f"📂 {m.upper()}", key=f"m_{m}", use_container_width=True):
                st.session_state.wybrane_miejsce = m
                st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ MIEJSCA", use_container_width=True):
                st.session_state.wybrane_miejsce = None
                st.rerun()
        with col2:
            if st.button("🏠 MENU", use_container_width=True): zmien_strone("Menu")
        
        miejsce = st.session_state.wybrane_miejsce
        st.header(f"📍 {miejsce.upper()}")
        with st.expander("➕ Dodaj produkt"):
            with st.form("quick_add", clear_on_submit=True):
                nowy = st.text_input("Nazwa:")
                if st.form_submit_button("Zapisz"):
                    if nowy:
                        new_row = pd.DataFrame([{"Produkt": nowy, "Stan": "Mamy", "Miejsce": miejsce}])
                        updated_df = pd.concat([df_spizarnia, new_row], ignore_index=True)
                        conn.update(worksheet="Spizarnia", data=updated_df)
                        refresh_all()

        st.divider()
        produkty = df_spizarnia[df_spizarnia['Miejsce'] == miejsce]
        for index, row in produkty.iterrows():
            ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
            if st.button(f"{ikona} {row['Produkt']}", key=f"s_{index}_{row['Produkt']}", use_container_width=True):
                df_spizarnia.at[index, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                refresh_all()

# --- SEKCJA 3: DANIA OBIADOWE ---
elif st.session_state.page == "Dania":
    if st.button("⬅️ MENU", use_container_width=True): zmien_strone("Menu")
    st.title("🥘 PRZEPISY")
    t1, t2 = st.tabs(["Twoje Dania", "Dodaj Przepis"])
    with t2:
        with st.form("f_dania"):
            n_dania = st.text_input("Nazwa:")
            skl = st.text_area("Składniki (po przecinku):")
            if st.form_submit_button("Zapisz"):
                new_d = pd.DataFrame([{"Nazwa": n_dania, "Skladniki": skl}])
                df_dania = pd.concat([df_dania, new_d], ignore_index=True)
                conn.update(worksheet="Dania", data=df_dania)
                refresh_all()
    with t1:
        for idx, d in df_dania.iterrows():
            with st.expander(f"🍴 {str(d['Nazwa']).upper()}"):
                st.write(d['Skladniki'])

# --- SEKCJA 4: PLAN POSIŁKÓW ---
elif st.session_state.page == "Plan":
    if st.button("⬅️ MENU", use_container_width=True): zmien_strone("Menu")
    st.title("📅 PLAN TYGODNIOWY")
    
    dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
    
    with st.expander("➕ DODAJ POSIŁEK DO PLANU"):
        if df_dania.empty:
            st.warning("Najpierw dodaj jakieś przepisy w sekcji 'Dania Obiadowe'!")
        else:
            with st.form("form_plan"):
                wybrany_dzien = st.selectbox("Dzień:", dni)
                wybrane_danie_nazwa = st.selectbox("Danie:", df_dania['Nazwa'].unique())
                if st.form_submit_button("Dodaj do planu i sprawdź braki"):
                    nowy_plan = pd.DataFrame([{"Dzien": wybrany_dzien, "Danie": wybrane_danie_nazwa}])
                    df_plan = pd.concat([df_plan, nowy_plan], ignore_index=True)
                    conn.update(worksheet="Plan", data=df_plan)
                    
                    przepis = df_dania[df_dania['Nazwa'] == wybrane_danie_nazwa].iloc[0]
                    skladniki = [s.strip() for s in str(przepis['Skladniki']).split(',')]
                    
                    for s in skladniki:
                        istniejacy = df_spizarnia[df_spizarnia['Produkt'].str.contains(s, case=False, na=False)]
                        if istniejacy.empty:
                            nowy_p = pd.DataFrame([{"Produkt": s, "Stan": "Brak", "Miejsce": "Inne"}])
                            df_spizarnia = pd.concat([df_spizarnia, nowy_p], ignore_index=True)
                        else:
                            # Jeśli planujemy, to upewniamy się, że braki są zaznaczone na liście zakupów
                            if (istniejacy['Stan'] != "Mamy").all():
                                df_spizarnia.loc[df_spizarnia['Produkt'].str.contains(s, case=False, na=False), 'Stan'] = "Brak"
                    
                    conn.update(worksheet="Spizarnia", data=df_spizarnia)
                    refresh_all()

    st.divider()
    
    # Wyświetlanie kalendarza z kropkami
    for d in dni:
        posilki_dnia = df_plan[df_plan['Dzien'] == d]
        if not posilki_dnia.empty:
            st.subheader(f"🗓️ {d}")
            for idx, p in posilki_dnia.iterrows():
                # --- LOGIKA SPRAWDZANIA KROPKI ---
                # Szukamy przepisu dla tego dania
                danie_info = df_dania[df_dania['Nazwa'] == p['Danie']]
                ikona_posilku = "⚪" # domyślna jeśli nie ma przepisu
                
                if not danie_info.empty:
                    skladniki_posilku = [s.strip() for s in str(danie_info.iloc[0]['Skladniki']).split(',')]
                    czy_kompletne = True
                    for skladnik in skladniki_posilku:
                        # Sprawdzamy czy mamy produkt w spizarni ze stanem "Mamy"
                        ma_na_stanie = df_spizarnia[(df_spizarnia['Produkt'].str.contains(skladnik, case=False, na=False)) & (df_spizarnia['Stan'] == "Mamy")]
                        if ma_na_stanie.empty:
                            czy_kompletne = False
                            break
                    ikona_posilku = "🟢" if czy_kompletne else "🔴"
                
                # --- WYŚWIETLANIE ---
                col_p, col_del = st.columns([4, 1])
                col_p.write(f"{ikona_posilku} {p['Danie']}")
                if col_del.button("❌", key=f"del_plan_{idx}"):
                    df_plan = df_plan.drop(idx)
                    conn.update(worksheet="Plan", data=df_plan)
                    refresh_all()
            st.write("---")

    if not df_plan.empty:
        if st.button("🗑️ WYCZYŚĆ CAŁY PLAN", use_container_width=True):
            df_plan = pd.DataFrame(columns=["Dzien", "Danie"])
            conn.update(worksheet="Plan", data=df_plan)
            refresh_all()
