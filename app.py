import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Moja Inteligentna Spizarnia", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

page = st.sidebar.radio("Wybierz sekcje:", ["Spizarnia", "Lista Zakupow", "Obiady"])

if page == "Spizarnia":
    st.title("Twoja Spizarnia")
    # Sekcja dodawania nowego produktu
    with st.expander("➕ Dodaj nowy produkt"):
        nowy_produkt = st.text_input("Nazwa produktu")
        nowa_kategoria = st.selectbox("Kategoria", ["Lodowka", "Zamrazarka", "Szafka", "Inne"])
        
        if st.button("Zapisz w spizarni"):
            if nowy_produkt:
                # Tworzymy nową linię danych
                nowy_wiersz = pd.DataFrame([{"Produkt": nowy_produkt, "Kategoria": nowa_kategoria, "Stan": "Mamy"}])
                # Pobieramy obecne dane i doklejamy nową linię
                df_aktualny = conn.read(worksheet="Spizarnia")
                df_nowy = pd.concat([df_aktualny, nowy_wiersz], ignore_index=True)
                # Wysyłamy z powrotem do Google Sheets
                conn.update(worksheet="Spizarnia", data=df_nowy)
                st.success(f"Dodano {nowy_produkt}!")
                st.cache_data.clear() # Czyścimy pamięć, żeby od razu było widać zmiany
            else:
                st.error("Wpisz nazwę produktu!")  
    try:
        df = conn.read(worksheet="Spizarnia")
        for index, row in df.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(row['Produkt'])
            col2.write(row['Kategoria'])
            if row['Stan'] == "Mamy":
                col3.success("Jest")
            else:
                col3.error("Brak")
    except Exception as e:
        st.error("Blad: Sprawdz czy zakladka nazywa sie Spizarnia")

elif page == "Obiady":
    st.title("Co na obiad?")
    try:
        df_s = conn.read(worksheet="Spizarnia")
        df_p = conn.read(worksheet="Przepisy")
        dania = df_p['Danie'].unique()
        wybor = st.selectbox("Wybierz danie:", dania)
        if st.button("Sprawdz skladniki"):
            potrzebne = df_p[df_p['Danie'] == wybor]['Skladnik'].tolist()
            mamy = df_s[df_s['Stan'] == 'Mamy']['Produkt'].tolist()
            braki = [s for s in potrzebne if s not in mamy]
            if not braki:
                st.success("Masz wszystko!")
            else:
                st.warning(f"Brakuje: {', '.join(braki)}")
    except:
        st.error("Blad: Sprawdz zakladke Przepisy")

elif page == "Lista Zakupow":
    st.title("Lista Zakupow")
    try:
        df = conn.read(worksheet="Spizarnia")
        braki = df[df['Stan'] != "Mamy"]['Produkt'].tolist()
        if braki:
            for b in braki:
                st.write(f"- {b}")
        else:
            st.success("Wszystko masz!")
    except:
        st.write("Problem z danymi")