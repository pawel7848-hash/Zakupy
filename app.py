import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA (Musi być na samym początku)
st.set_page_config(page_title="Kuchnia 2.0", layout="centered")

# Inicjalizacja stanów sesji (pamięć aplikacji)
if 'page' not in st.session_state:
    st.session_state.page = "Menu"
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

# POŁĄCZENIE
conn = st.connection("gsheets", type=GSheetsConnection)

# FUNKCJE POBIERANIA DANYCH (Zoptymalizowane cache)
@st.cache_data(ttl=10) # Dane żyją 10 sekund, potem są odświeżane
def get_data(sheet_name):
    data = conn.read(worksheet=sheet_name)
    data.columns = data.columns.str.strip()
    return data

def refresh_all():
    st.cache_data.clear()
    st.rerun()

# POBIERAMY DANE
df_spizarnia = get_data("Spizarnia")
try:
    df_dania = get_data("Dania")
except:
    df_dania = pd.DataFrame(columns=["Nazwa", "Skladniki"])

# --- NAWIGACJA ---
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

# --- SEKCJA 1: LISTA ZAKUPÓW ---
elif st.session_state.page == "Lista":
    if st.button("⬅️ POWRÓT DO MENU", use_container_width=True): zmien_strone("Menu")
    st.title("🛒 DO KUPIENIA")
    
    braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
    if not braki.empty:
        for index, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']} ({row.get('Miejsce', 'Brak')})", key=f"k_{index}", use_container_width=True):
                df_spizarnia.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                refresh_all()
    else:
        st.success("Wszystko kupione! 🎉")

# --- SEKCJA 2: STAN SPIŻARNI ---
# --- SEKCJA 2: STAN SPIŻARNI ---
elif st.session_state.page == "Spizarnia":
    # 1. WIDOK LISTY MIEJSC (Szafka, Lodówka itd.)
    if st.session_state.wybrane_miejsce is None:
        if st.button("🏠 POWRÓT DO MENU GŁÓWNEGO", use_container_width=True):
            zmien_strone("Menu")
            st.rerun()
            
        st.title("📦 WYBIERZ MIEJSCE")
        miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
        for m in miejsca:
            if st.button(f"📂 {m.upper()}", key=f"m_{m}", use_container_width=True):
                st.session_state.wybrane_miejsce = m
                st.rerun()

    # 2. WIDOK WNĘTRZA MIEJSCA (np. Jesteś w Lodówce)
    else:
        # Dwa przyciski nawigacyjne obok siebie
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ DO MIEJSC", use_container_width=True):
                st.session_state.wybrane_miejsce = None
                st.rerun()
        with col2:
            if st.button("🏠 DO MENU", use_container_width=True):
                zmien_strone("Menu")
                st.rerun()
        
        miejsce = st.session_state.wybrane_miejsce
        st.header(f"📍 {miejsce.upper()}")

        # Sekcja dodawania produktu
        with st.expander("➕ Dodaj produkt tutaj"):
            with st.form("quick_add", clear_on_submit=True):
                nowy = st.text_input("Nazwa produktu:")
                if st.form_submit_button("Zapisz"):
                    if nowy:
                        new_row = pd.DataFrame([{"Produkt": nowy, "Stan": "Mamy", "Miejsce": miejsce}])
                        updated_df = pd.concat([df_spizarnia, new_row], ignore_index=True)
                        conn.update(worksheet="Spizarnia", data=updated_df)
                        refresh_all()

        st.divider()
        
        # Lista produktów w danym miejscu
        produkty = df_spizarnia[df_spizarnia['Miejsce'] == miejsce]
        for index, row in produkty.iterrows():
            ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
            if st.button(f"{ikona} {row['Produkt']}", key=f"s_{index}", use_container_width=True):
                df_spizarnia.at[index, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                refresh_all()

        st.divider()
        produkty = df_spizarnia[df_spizarnia['Miejsce'] == miejsce]
        for index, row in produkty.iterrows():
            ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
            if st.button(f"{ikona} {row['Produkt']}", key=f"s_{index}", use_container_width=True):
                # Szybka zmiana stanu
                df_spizarnia.at[index, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                refresh_all()

# --- SEKCJA 3: DANIA OBIADOWE ---
elif st.session_state.page == "Dania":
    if st.button("⬅️ MENU", use_container_width=True): zmien_strone("Menu")
    st.title("🥘 DANIA OBIADOWE")

    tab1, tab2 = st.tabs(["Twoje Dania", "Dodaj Przepis"])

    with tab2:
        with st.form("f_dania"):
            n_dania = st.text_input("Nazwa (np. Schabowe):")
            skl = st.text_area("Składniki (po przecinku):")
            if st.form_submit_button("Zapisz"):
                new_d = pd.DataFrame([{"Nazwa": n_dania, "Skladniki": skl}])
                df_dania = pd.concat([df_dania, new_d], ignore_index=True)
                conn.update(worksheet="Dania", data=df_dania)
                refresh_all()

    with tab1:
        for idx, d in df_dania.iterrows():
            with st.expander(f"🍴 {d['Nazwa'].upper()}"):
                skladniki = [s.strip() for s in d['Skladniki'].split(',')]
                st.write(", ".join(skladniki))
                
                if st.button(f"Sprawdź braki", key=f"ch_{idx}", use_container_width=True):
                    braki = []
                    for s in skladniki:
                        # Szukamy czy mamy dany produkt w spizarni
                        ma_na_stanie = df_spizarnia[(df_spizarnia['Produkt'].str.contains(s, case=False, na=False)) & (df_spizarnia['Stan'] == "Mamy")]
                        if ma_na_stanie.empty:
                            braki.append(s)
                    
                    if not braki:
                        st.success("Wszystko jest! Gotuj śmiało.")
                    else:
                        st.warning("Brakuje: " + ", ".join(braki))
                        if st.button("Dodaj braki do listy", key=f"add_br_{idx}", use_container_width=True):
                            for b in braki:
                                # Jeśli produktu nie ma wcale w spizarni - dodaj go jako "Brak"
                                if df_spizarnia[df_spizarnia['Produkt'].str.contains(b, case=False, na=False)].empty:
                                    nowy_b = pd.DataFrame([{"Produkt": b, "Stan": "Brak", "Miejsce": "Inne"}])
                                    df_spizarnia = pd.concat([df_spizarnia, nowy_b], ignore_index=True)
                                else:
                                    # Jeśli jest, zmień stan na "Brak"
                                    df_spizarnia.loc[df_spizarnia['Produkt'].str.contains(b, case=False, na=False), 'Stan'] = "Brak"
                            
                            conn.update(worksheet="Spizarnia", data=df_spizarnia)
                            refresh_all()

