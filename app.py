import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Moja Spiżarnia", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

# Inicjalizacja stanów sesji (pamięć aplikacji)
if 'page' not in st.session_state:
    st.session_state.page = "Menu"
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

# Funkcja pomocnicza do zmiany stron
def zmien_strone(nazwa):
    st.session_state.page = nazwa
    st.session_state.wybrane_miejsce = None

# POBIERANIE DANYCH
df = conn.read(worksheet="Spizarnia", ttl=0)
df.columns = df.columns.str.strip()

# --- STRONA GŁÓWNA (MENU ZAMIAST SIDEBARU) ---
if st.session_state.page == "Menu":
    st.title("🏠 SPIŻARNIA DOMOWA")
    st.write("---")
    
    # Duże przyciski nawigacyjne
    if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True):
        zmien_strone("Lista")
        st.rerun()
        
    if st.button("📦 STAN SPIŻARNI", use_container_width=True):
        zmien_strone("Spizarnia")
        st.rerun()
        
    if st.button("➕ DODAJ PRODUKT", use_container_width=True):
        zmien_strone("Dodaj")
        st.rerun()

# --- SEKCJA 1: LISTA ZAKUPÓW ---
elif st.session_state.page == "Lista":
    if st.button("⬅️ WRÓĆ DO MENU", use_container_width=True):
        zmien_strone("Menu")
        st.rerun()
        
    st.title("🛒 DO KUPIENIA")
    braki = df[df['Stan'] != "Mamy"]
    
    if not braki.empty:
        for index, row in braki.iterrows():
            label = f"🔴 {row['Produkt']} ({row.get('Miejsce', 'Brak')})"
            if st.button(label, key=f"kup_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()
    else:
        st.success("Wszystko kupione! 🎉")

# --- SEKCJA 2: STAN SPIŻARNI ---
elif st.session_state.page == "Spizarnia":
    # Przycisk powrotu (zależny od tego czy jesteśmy w folderze czy nie)
    if st.session_state.wybrane_miejsce is None:
        if st.button("⬅️ WRÓĆ DO MENU", use_container_width=True):
            zmien_strone("Menu")
            st.rerun()
        st.title("📦 WYBIERZ MIEJSCE")
        lista_miejsc = sorted(df['Miejsce'].fillna('Inne').unique())
        for m in lista_miejsc:
            if st.button(f"📂 {m.upper()}", key=f"loc_{m}", use_container_width=True):
                st.session_state.wybrane_miejsce = m
                st.rerun()
    else:
        if st.button("⬅️ WRÓĆ DO MIEJSC", use_container_width=True):
            st.session_state.wybrane_miejsce = None
            st.rerun()
        
        miejsce = st.session_state.wybrane_miejsce
        st.title(f"📍 {miejsce.upper()}")
        st.divider()

        produkty = df[df['Miejsce'].fillna('Inne') == miejsce]
        for index, row in produkty.iterrows():
            ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
            label = f"{ikona} {row['Produkt']}"
            if st.button(label, key=f"st_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()

# --- SEKCJA 3: DODAJ PRODUKT ---
elif st.session_state.page == "Dodaj":
    if st.button("⬅️ WRÓĆ DO MENU", use_container_width=True):
        zmien_strone("Menu")
        st.rerun()
        
    st.title("➕ NOWY PRODUKT")
    with st.form("add_form", clear_on_submit=True):
        nowy_produkt = st.text_input("Nazwa produktu:")
        istniejace_miejsca = sorted(df['Miejsce'].fillna('Inne').unique()) if 'Miejsce' in df.columns else []
        nowe_miejsce = st.selectbox("Wybierz miejsce:", istniejace_miejsca)
        dodatkowe_miejsce = st.text_input("Lub wpisz nowe miejsce:")
        
        if st.form_submit_button("Dodaj do bazy"):
            if nowy_produkt:
                miejsce_final = dodatkowe_miejsce if dodatkowe_miejsce else nowe_miejsce
                nowy_wiersz = pd.DataFrame([{"Produkt": nowy_produkt, "Stan": "Mamy", "Miejsce": miejsce_final}])
                df = pd.concat([df, nowy_wiersz], ignore_index=True)
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.success(f"Dodano {nowy_produkt}!")
