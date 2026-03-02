import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. KONFIGURACJA
st.set_page_config(page_title="Spiżarnia", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. PASEK BOCZNY (MENU)
with st.sidebar:
    st.title("MENU")
    page = st.radio("Wybierz sekcję:", ["Lista Zakupow", "Stan Spizarni", "Dodaj Produkt"])

# --- SEKCJA 1: LISTA ZAKUPÓW (Ta nowa, co działa) ---
if page == "Lista Zakupow":
    st.title("🛒 TWOJA LISTA")
    df = conn.read(worksheet="Spizarnia")
    braki = df[df['Stan'] != "Mamy"]

    if not braki.empty:
        for index, row in braki.iterrows():
            # TYLKO PRZYCISK - bez dodatkowych napisów!
            label = f"🔴 {row['Produkt']} ({row['Kategoria']})"
            if st.button(label, key=f"list_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()
    else:
        st.success("Wszystko kupione! 🎉")

# --- SEKCJA 2: STAN SPIŻARNI ---
elif page == "Stan Spizarni":
    st.title("📦 STAN MAGAZYNOWY")
    df = conn.read(worksheet="Spizarnia")
    # Pokazujemy wszystko co "Mamy"
    mamy = df[df['Stan'] == "Mamy"]
    st.dataframe(mamy, use_container_width=True)

# --- SEKCJA 3: DODAJ PRODUKT ---
elif page == "Dodaj Produkt":
    st.title("➕ DODAJ DO BAZY")
    # Tutaj wklej swój stary kod do formularza (st.form), jeśli go pamiętasz
    # Jeśli nie, daj znać, napiszę Ci nowy formularz do dodawania.
    st.write("Tu zaraz przywrócimy Twój formularz.")
