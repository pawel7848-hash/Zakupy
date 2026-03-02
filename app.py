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
            
            if row['Stan'] == "Mamy":
                status_icon = "🟢"
                button_label = "Brak! 🛒"
                new_status = "Brak"
            else:
                status_icon = "🔴"
                button_label = "Kupione! ✅"
                new_status = "Mamy"

            col1.write(f"{status_icon} **{row['Produkt']}**")
            col2.write(f"_{row['Kategoria']}_")
            
            if col3.button(button_label, key=f"btn_{index}"):
                df.at[index, 'Stan'] = new_status
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()

    except Exception as e:
        st.error(f"Problem z tabelą: {e}")

elif page == "Lista Zakupow":
    st.title("🛒 Lista")

    try:
        df = conn.read(worksheet="Spizarnia")
        braki = df[df['Stan'] != "Mamy"]

        if not braki.empty:
            for index, row in braki.iterrows():
                col_txt, col_btn = st.columns([4, 1])
                # Poprawione: unsafe_allow_html=True zamiast unsafe_allow_index
                col_txt.markdown(f"🔴 **{row['Produkt']}** <small>({row['Kategoria']})</small>", unsafe_allow_html=True)
                
                if col_btn.button("✅", key=f"shop_{index}"):
                    df.at[index, 'Stan'] = "Mamy"
                    conn.update(worksheet="Spizarnia", data=df)
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.success("Lodówka pełna! 🎉")
            
    except Exception as e:
        st.error(f"Błąd: {e}")

elif page == "Lista Zakupow":
    st.title("🛒 Lista")

    try:
        df = conn.read(worksheet="Spizarnia")
        braki = df[df['Stan'] != "Mamy"]

        if not braki.empty:
            # Tworzymy listę wyboru (Selectbox), która zajmuje tylko JEDNĄ linię na telefonie
            # Wybierasz produkt z listy i klikasz JEDEN przycisk pod spodem, żeby go "odznaczyć"
            wybrany = st.selectbox("Wybierz co kupiłeś:", braki['Produkt'].tolist())
            
            if st.button(f"Zatwierdź: {wybrany}", use_container_width=True):
                # Szukamy indeksu wybranego produktu
                idx = df[df['Produkt'] == wybrany].index[0]
                df.at[idx, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()

            st.write("---")
            st.write("**Pozostało do kupienia:**")
            # Wyświetlamy resztę jako zwykły tekst (bardzo ciasno)
            for _, row in braki.iterrows():
                st.markdown(f"🔴 {row['Produkt']} <small>({row['Kategoria']})</small>", unsafe_allow_html=True)
                
        else:
            st.success("Wszystko kupione! 🎉")
            
    except Exception as e:
        st.error(f"Błąd: {e}")