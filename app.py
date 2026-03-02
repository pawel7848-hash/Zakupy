import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Moja Spiżarnia", layout="centered")

# ttl=0 wymusza pobieranie świeżych danych z Google Sheets przy każdym odświeżeniu
conn = st.connection("gsheets", type=GSheetsConnection)

# Inicjalizacja nawigacji wewnątrz spiżarni
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

# 2. POBIERANIE DANYCH
df = conn.read(worksheet="Spizarnia", ttl=0)
# Czyścimy nazwy kolumn z ewentualnych spacji
df.columns = df.columns.str.strip()

# 3. MENU BOCZNE
with st.sidebar:
    st.title("MENU")
    nowa_strona = st.radio("Wybierz sekcję:", ["Lista Zakupów", "Stan Spiżarni", "Dodaj Produkt"])
    if nowa_strona != "Stan Spiżarni":
        st.session_state.wybrane_miejsce = None
    page = nowa_strona

# --- SEKCJA 1: LISTA ZAKUPÓW (Tylko to, co ma stan "Brak") ---
if page == "Lista Zakupów":
    st.title("🛒 DO KUPIENIA")
    braki = df[df['Stan'] != "Mamy"]
    
    if not braki.empty:
        for index, row in braki.iterrows():
            # Kliknięcie tutaj zmienia stan na "Mamy" (oznacza, że kupione)
            label = f"🔴 {row['Produkt']} ({row.get('Miejsce', 'Brak')})"
            if st.button(label, key=f"kup_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()
    else:
        st.success("Wszystko kupione! 🎉")

# --- SEKCJA 2: STAN SPIŻARNI (WSZYSTKIE PRZEDMIOTY) ---
elif page == "Stan Spiżarni":
    # Sprawdzamy czy kolumna Miejsce istnieje
    if 'Miejsce' not in df.columns:
        st.error("Nie widzę kolumny 'Miejsce' w Twoim arkuszu Google!")
    else:
        # MENU WYBORU MIEJSCA
        if st.session_state.wybrane_miejsce is None:
            st.title("📦 TWOJE MIEJSCA")
            lista_miejsc = sorted(df['Miejsce'].fillna('Inne').unique())
            for m in lista_miejsc:
                if st.button(f"📂 {m.upper()}", key=f"loc_{m}", use_container_width=True):
                    st.session_state.wybrane_miejsce = m
                    st.rerun()
        
        # WIDOK PRZEDMIOTÓW W WYBRANYM MIEJSCU
        else:
            miejsce = st.session_state.wybrane_miejsce
            st.title(f"📍 {miejsce.upper()}")
            
            if st.button("⬅️ Wróć do listy miejsc", use_container_width=True):
                st.session_state.wybrane_miejsce = None
                st.rerun()
            
            st.divider()

            # Pokazujemy WSZYSTKIE produkty z tego miejsca
            produkty_w_miejscu = df[df['Miejsce'].fillna('Inne') == miejsce]
            
            for index, row in produkty_w_miejscu.iterrows():
                # Ustalamy ikonkę na podstawie stanu
                ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
                nowy_stan = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                
                label = f"{ikona} {row['Produkt']}"
                
                # Kliknięcie przełącza stan (Mamy <-> Brak)
                if st.button(label, key=f"stan_{index}", use_container_width=True):
                    df.at[index, 'Stan'] = nowy_stan
                    conn.update(worksheet="Spizarnia", data=df)
                    st.cache_data.clear()
                    st.rerun()

# --- SEKCJA 3: DODAJ PRODUKT ---
elif page == "Dodaj Produkt":
    st.title("➕ NOWY PRODUKT")
    with st.form("add_form", clear_on_submit=True):
        nowy_produkt = st.text_input("Nazwa produktu:")
        nowe_miejsce = st.selectbox("Gdzie to leży?", sorted(df['Miejsce'].fillna('Inne').unique()) if 'Miejsce' in df.columns else ["Lodówka", "Szafka"])
        submit = st.form_submit_button("Dodaj do bazy")
        
        if submit and nowy_produkt:
            nowy_wiersz = pd.DataFrame([{"Produkt": nowy_produkt, "Stan": "Mamy", "Miejsce": nowe_miejsce}])
            df = pd.concat([df, nowy_wiersz], ignore_index=True)
            conn.update(worksheet="Spizarnia", data=df)
            st.cache_data.clear()
            st.success(f"Dodano {nowy_produkt} do {nowe_miejsce}!")
