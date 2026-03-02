import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Moja Inteligentna Spizarnia", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

page = st.sidebar.radio("Wybierz sekcje:", ["Spizarnia", "Lista Zakupow", "Obiady"])

if page == "Spizarnia":
    st.title("Twoja Spizarnia")
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