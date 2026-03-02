import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. KONFIGURACJA
st.set_page_config(page_title="Spiżarnia", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. MENU BOCZNE
with st.sidebar:
    st.title("MENU")
    page = st.radio("Wybierz sekcję:", ["Lista Zakupów", "Stan Spiżarni", "Dodaj Produkt"])

# Pobieramy dane raz dla wszystkich sekcji
df = conn.read(worksheet="Spizarnia")

# --- SEKCJA 1: LISTA ZAKUPÓW (To, czego NIE MAMY) ---
if page == "Lista Zakupów":
    st.title("🛒 DO KUPIENIA")
    braki = df[df['Stan'] != "Mamy"]

    if not braki.empty:
        for index, row in braki.iterrows():
            label = f"🔴 {row['Produkt']} ({row['Kategoria']})"
            if st.button(label, key=f"kup_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()
    else:
        st.success("Wszystko kupione! 🎉")

# --- SEKCJA 2: STAN SPIŻARNI (To, co MAMY - tu też dodajemy przyciski!) ---
elif page == "Stan Spiżarni":
    st.title("📦 MAMY W DOMU")
    st.info("Kliknij w produkt, żeby dodać go do listy zakupów:")
    
    mamy = df[df['Stan'] == "Mamy"]

    if not mamy.empty:
        for index, row in mamy.iterrows():
            # Zielony przycisk - oznacza, że produkt jest w domu. 
            # Kliknięcie zmienia stan na "Brak", czyli wrzuca na listę.
            label = f"🟢 {row['Produkt']} ({row['Kategoria']})"
            if st.button(label, key=f"stan_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Brak"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()
    else:
        st.warning("Spiżarnia jest pusta! Dodaj coś do listy.")

# --- SEKCJA 3: DODAJ PRODUKT ---
elif page == "Dodaj Produkt":
    st.title("➕ NOWY PRODUKT")
    with st.form("add_form", clear_on_submit=True):
        nowy_produkt = st.text_input("Nazwa produktu:")
        nowa_kategoria = st.selectbox("Kategoria:", ["Warzywa", "Owoce", "Nabiał", "Mięso", "Napoje", "Inne"])
        submit = st.form_submit_button("Dodaj do bazy")
        
        if submit and nowy_produkt:
            import pandas as pd
            nowy_wiersz = pd.DataFrame([{"Produkt": nowy_produkt, "Kategoria": nowa_kategoria, "Stan": "Brak"}])
            df = pd.concat([df, nowy_wiersz], ignore_index=True)
            conn.update(worksheet="Spizarnia", data=df)
            st.cache_data.clear()
            st.success(f"Dodano {nowy_produkt}!")
