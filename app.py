import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Moja Spiżarnia", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

# Pamięć aplikacji
if 'page' not in st.session_state:
    st.session_state.page = "Menu"
if 'wybrane_miejsce' not in st.session_state:
    st.session_state.wybrane_miejsce = None

def zmien_strone(nazwa):
    st.session_state.page = nazwa
    st.session_state.wybrane_miejsce = None

# POBIERANIE DANYCH
df_spizarnia = conn.read(worksheet="Spizarnia", ttl=0)
df_spizarnia.columns = df_spizarnia.columns.str.strip()

# Pobieranie dań (zakładka "Dania" w Excelu: Kolumny: Nazwa, Skladniki)
try:
    df_dania = conn.read(worksheet="Dania", ttl=0)
except:
    df_dania = pd.DataFrame(columns=["Nazwa", "Skladniki"])

# --- MENU GŁÓWNE ---
if st.session_state.page == "Menu":
    st.title("🏠 KUCHNIA")
    if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): zmien_strone("Lista")
    if st.button("📦 STAN SPIŻARNI", use_container_width=True): zmien_strone("Spizarnia")
    if st.button("🥘 DANIA OBIADOWE", use_container_width=True): zmien_strone("Dania")

# --- SEKCJA 1: LISTA ZAKUPÓW ---
elif st.session_state.page == "Lista":
    if st.button("⬅️ MENU", use_container_width=True): zmien_strone("Menu")
    st.title("🛒 DO KUPIENIA")
    braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
    for index, row in braki.iterrows():
        if st.button(f"🔴 {row['Produkt']} ({row.get('Miejsce', 'Brak')})", key=f"k_{index}", use_container_width=True):
            df_spizarnia.at[index, 'Stan'] = "Mamy"
            conn.update(worksheet="Spizarnia", data=df_spizarnia)
            st.cache_data.clear()
            st.rerun()

# --- SEKCJA 2: STAN SPIŻARNI ---
elif st.session_state.page == "Spizarnia":
    if st.session_state.wybrane_miejsce is None:
        if st.button("⬅️ MENU", use_container_width=True): zmien_strone("Menu")
        st.title("📦 WYBIERZ MIEJSCE")
        miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
        for m in miejsca:
            if st.button(f"📂 {m.upper()}", key=f"m_{m}", use_container_width=True):
                st.session_state.wybrane_miejsce = m
                st.rerun()
    else:
        if st.button("⬅️ WRÓĆ DO MIEJSC", use_container_width=True):
            st.session_state.wybrane_miejsce = None
            st.rerun()
        
        miejsce = st.session_state.wybrane_miejsce
        st.title(f"📍 {miejsce.upper()}")

        # DODAWANIE DO TEGO KONKRETNEGO MIEJSCA
        with st.expander("➕ Dodaj produkt tutaj"):
            nowy = st.text_input("Nazwa produktu:")
            if st.button("Zapisz w " + miejsce):
                nowy_wiersz = pd.DataFrame([{"Produkt": nowy, "Stan": "Mamy", "Miejsce": miejsce}])
                df_spizarnia = pd.concat([df_spizarnia, nowy_wiersz], ignore_index=True)
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                st.cache_data.clear()
                st.rerun()

        st.divider()
        produkty = df_spizarnia[df_spizarnia['Miejsce'] == miejsce]
        for index, row in produkty.iterrows():
            ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
            if st.button(f"{ikona} {row['Produkt']}", key=f"s_{index}", use_container_width=True):
                df_spizarnia.at[index, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                st.cache_data.clear()
                st.rerun()

# --- SEKCJA 3: DANIA OBIADOWE ---
elif st.session_state.page == "Dania":
    if st.button("⬅️ MENU", use_container_width=True): zmien_strone("Menu")
    st.title("🥘 DANIA OBIADOWE")

    tab1, tab2 = st.tabs(["Twoje Dania", "Dodaj Przepis"])

    with tab2:
        with st.form("form_dania"):
            nazwa_dania = st.text_input("Nazwa dania (np. Schabowe):")
            skladniki = st.text_area("Składniki (oddziel przecinkiem, np: Schab, Jajka, Bułka tarta):")
            if st.form_submit_button("Zapisz Danie"):
                nowe_danie = pd.DataFrame([{"Nazwa": nazwa_dania, "Skladniki": skladniki}])
                df_dania = pd.concat([df_dania, nowe_danie], ignore_index=True)
                conn.update(worksheet="Dania", data=df_dania)
                st.success("Danie dodane!")

    with tab1:
        for idx, danie in df_dania.iterrows():
            with st.expander(f"🍴 {danie['Nazwa'].upper()}"):
                lista_skladnikow = [s.strip() for s in danie['Skladniki'].split(',')]
                st.write("**Składniki:** " + ", ".join(lista_skladnikow))
                
                if st.button(f"Sprawdź braki dla: {danie['Nazwa']}", key=f"check_{idx}"):
                    braki_do_dodania = []
                    for s in lista_skladnikow:
                        # Sprawdzamy czy skladnik jest w spizarni i czy go mamy
                        match = df_spizarnia[df_spizarnia['Produkt'].str.contains(s, case=False, na=False)]
                        if match.empty or (match['Stan'] != "Mamy").all():
                            braki_do_dodania.append(s)
                    
                    if not braki_do_dodania:
                        st.success("Masz wszystko w domu! Można gotować. 👨‍🍳")
                    else:
                        st.warning("Brakuje: " + ", ".join(braki_do_dodania))
                        if st.button("Dodaj braki do listy zakupów", key=f"add_br_{idx}"):
                            for b in braki_do_dodania:
                                # Jeśli nie ma w ogóle w spizarni, dopisz jako Brak
                                if df_spizarnia[df_spizarnia['Produkt'].str.contains(b, case=False, na=False)].empty:
                                    nowy_b = pd.DataFrame([{"Produkt": b, "Stan": "Brak", "Miejsce": "Inne"}])
                                    df_spizarnia = pd.concat([df_spizarnia, nowy_b], ignore_index=True)
                                else:
                                    # Jeśli jest, ale stan "Mamy" jest False, to już i tak jest na liście
                                    df_spizarnia.loc[df_spizarnia['Produkt'].str.contains(b, case=False, na=False), 'Stan'] = "Brak"
                            
                            conn.update(worksheet="Spizarnia", data=df_spizarnia)
                            st.cache_data.clear()
                            st.success("Dodano braki do listy!")
