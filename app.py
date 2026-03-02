import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Ustawienia wyglądu strony
st.set_page_config(page_title="Moja Spiżarnia", layout="centered")

st.title("🛒 Moja Spiżarnia (Live)")

# 1. Połączenie z Twoim Arkuszem Google
# Wykorzystuje dane, które wkleiłeś w Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Pobranie danych z Arkusza
# ttl="1m" oznacza, że aplikacja będzie sprawdzać zmiany w arkuszu co 1 minutę
df = conn.read(ttl="1m")

# 3. Wyświetlanie produktów
if not df.empty:
    st.subheader("Lista produktów:")
    for index, row in df.iterrows():
        # Tworzy checkbox dla każdego produktu z kolumny "Produkt"
        # Zaznacza go, jeśli w kolumnie "Czy_jest" wpisałeś TRUE
        st.checkbox(row['Produkt'], value=bool(row['Czy_jest']), key=f"prod_{index}")
else:
    st.warning("Twój arkusz jest pusty lub nie ma nagłówków 'Produkt' i 'Czy_jest'!")

st.write("---")
st.caption("Dane pobierane prosto z Google Sheets 🚀")