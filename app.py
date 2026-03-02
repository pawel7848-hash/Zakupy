import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Konfiguracja strony
st.set_page_config(page_title="Lista", layout="centered")

# Połączenie
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("MOJA NOWA LISTA")

try:
    df = conn.read(worksheet="Spizarnia")
    # Filtrujemy tylko to, czego nie ma
    braki = df[df['Stan'] != "Mamy"]

    if not braki.empty:
        for index, row in braki.iterrows():
            # TU JEST CAŁY TRYK:
            # Nazwa produktu jest etykietą przycisku (label).
            # Nie używamy st.write ani nic innego!
            etykieta = f"🛒 {row['Produkt']} ({row['Kategoria']})"
            
            if st.button(etykieta, key=f"btn_{index}", use_container_width=True):
                df.at[index, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df)
                st.cache_data.clear()
                st.rerun()
    else:
        st.success("Wszystko kupione! 🎉")
except Exception as e:
    st.error(f"Błąd: {e}")
