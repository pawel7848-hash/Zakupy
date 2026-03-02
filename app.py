import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Moja Inteligentna Spizarnia", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

page = st.sidebar.radio("Wybierz sekcje:", ["Spizarnia", "Lista Zakupow", "Obiady"])

if page == "Spizarnia":
    st.title("📦 Twoja Spizarnia")

    # 1. Formularz dodawania
    with st.expander("➕ Dodaj nowy produkt"):
        nowy_p = st.text_input("Nazwa produktu")
        nowa_k = st.selectbox("Kategoria", ["Lodowka", "Zamrazarka", "Szafka", "Inne"])
        if st.button("Zapisz w spizarni"):
            if nowy_p:
                df_akt = conn.read(worksheet="Spizarnia")
                nowy_w = pd.DataFrame([{"Produkt": nowy_p, "Kategoria": nowa_k, "Stan": "Mamy"}])
                df_nowy = pd.concat([df_akt, nowy_w], ignore_index=True)
                conn.update(worksheet="Spizarnia", data=df_nowy)
                st.cache_data.clear()
                st.rerun()

    st.write("---")

    try:
        df = conn.read(worksheet="Spizarnia")
        
        for index, row in df.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            # Sprawdzamy stan i dobieramy kolor/ikonę
            if row['Stan'] == "Mamy":
                status_icon = "🟢" # Zielona kropka
                button_label = "Zużyte! 🛒"
                new_status = "Brak"
            else:
                status_icon = "🔴" # Czerwona kropka
                button_label = "Kupione! ✅"
                new_status = "Mamy"

            # Wyświetlanie w rzędzie
            col1.write(f"{status_icon} **{row['Produkt']}**")
            col2.write(f"_{row['Kategoria']}_")
            
            # Przycisk zmiany stanu
            if col3.button(button_label, key=f"btn_{index}"):
                df.at[index, 'Stan'] = new_status
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()

    except Exception as e:
        st.error(f"Problem z tabelą: {e}")
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