import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Spiżarnia", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

# Inicjalizacja stanu sesji dla nawigacji wewnątrz spiżarni
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

# 2. MENU BOCZNE
with st.sidebar:
    st.title("MENU")
    # Resetujemy wybrane miejsce przy zmianie głównej strony
    nowa_strona = st.radio("Wybierz sekcję:", ["Lista Zakupów", "Stan Spiżarni", "Dodaj Produkt"])
    if nowa_strona != "Stan Spiżarni":
        st.session_state.wybrane_miejsce = None
    page = nowa_strona

# Pobieramy dane
df = conn.read(worksheet="Spizarnia")

# --- SEKCJA 1: LISTA ZAKUPÓW ---
if page == "Lista Zakupów":
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

# --- SEKCJA 2: STAN SPIŻARNI (POZIOMY: MIEJSCA -> PRODUKTY) ---
elif page == "Stan Spiżarni":
    mamy = df[df['Stan'] == "Mamy"]

    # JEŚLI NIE WYBRANO JESZCZE MIEJSCA - Pokaż listę lokalizacji
    if st.session_state.wybrane_miejsce is None:
        st.title("📦 WYBIERZ MIEJSCE")
        if not mamy.empty:
            lista_miejsc = sorted(mamy['Miejsce'].fillna('Inne').unique())
            for m in lista_miejsc:
                # Kliknięcie w nazwę miejsca (np. LODÓWKA) zapisuje ją w pamięci
                if st.button(f"📂 {m.upper()}", key=f"loc_{m}", use_container_width=True):
                    st.session_state.wybrane_miejsce = m
                    st.rerun()
        else:
            st.warning("Spiżarnia jest pusta!")

    # JEŚLI MIEJSCE JEST WYBRANE - Pokaż produkty w tym miejscu
    else:
        miejsce = st.session_state.wybrane_miejsce
        st.title(f"📍 {miejsce.upper()}")
        
        # Przycisk POWRÓT do listy miejsc
        if st.button("⬅️ Wróć do listy miejsc", use_container_width=True):
            st.session_state.wybrane_miejsce = None
            st.rerun()
        
        st.divider()

        produkty_w_miejscu = mamy[mamy['Miejsce'] == miejsce]
        for index, row in produkty_w_miejscu.iterrows():
            label = f"🟢 {row['Produkt']}"
            if st.button(label, key=f"stan_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Brak"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()

# --- SEKCJA 3: DODAJ PRODUKT ---
elif page == "Dodaj Produkt":
    st.title("➕ NOWY PRODUKT")
    with st.form("add_form", clear_on_submit=True):
        nowy_produkt = st.text_input("Nazwa produktu:")
        nowa_kategoria = st.selectbox("Kategoria:", ["Warzywa", "Owoce", "Nabiał", "Mięso", "Napoje", "Inne"])
        nowe_miejsce = st.text_input("Gdzie to leży? (np. Lodówka, Szafka 1)")
        submit = st.form_submit_button("Dodaj do bazy")
        
        if submit and nowy_produkt:
            nowy_wiersz = pd.DataFrame([{"Produkt": nowy_produkt, "Kategoria": nowa_kategoria, "Stan": "Brak", "Miejsce": nowe_miejsce}])
            df = pd.concat([df, nowy_wiersz], ignore_index=True)
            conn.update(worksheet="Spizarnia", data=df)
            st.cache_data.clear()
            st.success(f"Dodano {nowy_produkt}!")
