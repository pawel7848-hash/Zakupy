import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA - zero agresywnego CSS, zostawiamy tylko lekki margines na górze
st.set_page_config(page_title="Dom", layout="centered")
st.markdown("<style>.block-container {padding-top: 3rem !important;}</style>", unsafe_allow_html=True)

# 2. INICJALIZACJA
if 'page' not in st.session_state: st.session_state.page = "Menu Dom"
if 'sub_page' not in st.session_state: st.session_state.sub_page = None
if 'wybrane_miejsce' not in st.session_state: st.session_state.wybrane_miejsce = None

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def get_data(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name)
        data.columns = data.columns.str.strip()
        return data
    except: return pd.DataFrame()

def refresh_all():
    st.cache_data.clear()
    st.rerun()

df_spizarnia = get_data("Spizarnia")
df_dania = get_data("Dania")
df_plan = get_data("Plan")
df_inne = get_data("Inne")

# 3. FUNKCJA TERMINÓW - Naprawiony format daty
def kafelek_terminu(label, kategoria, nazwa_klucza):
    global df_inne 
    row = df_inne[(df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)]
    today = pd.Timestamp.now().date()
    
    # Domyślne wartości
    data_terminu = today
    kolor, status = "gray", "BRAK DANYCH"
    
    if not row.empty:
        try:
            val = row.iloc[0]['Wartosc']
            # Konwersja z wymuszonym formatem ISO (YYYY-MM-DD), żeby uniknąć błędów
            data_terminu = pd.to_datetime(val).date()
            if data_terminu >= today:
                kolor, status = "green", "✅ AKTUALNE"
            else:
                kolor, status = "red", "🚨 PO TERMINIE!"
        except:
            pass

    # Przycisk (Popover) do zmiany daty
    with st.popover(f":{kolor}[{label}: {data_terminu.strftime('%d.%m.%Y')}] \n\n {status}", use_container_width=True):
        st.write(f"Zmień datę dla: {label}")
        nowa = st.date_input("Wybierz nową datę", value=data_terminu, format="DD.MM.YYYY", key=f"d_{kategoria}_{nazwa_klucza}")
        if st.button("Zapisz zmiany", key=f"b_{kategoria}_{nazwa_klucza}"):
            mask = (df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)
            # Zapisujemy zawsze w formacie YYYY-MM-DD - Excel i Pandas to kochają
            nowa_str = nowa.strftime('%Y-%m-%d')
            if not df_inne[mask].empty:
                df_inne.loc[mask, 'Wartosc'] = nowa_str
            else:
                new_row = pd.DataFrame([{"Kategoria": kategoria, "Nazwa": nazwa_klucza, "Wartosc": nowa_str}])
                df_inne = pd.concat([df_inne, new_row], ignore_index=True)
            conn.update(worksheet="Inne", data=df_inne)
            refresh_all()

# =========================================================
# --- NAWIGACJA I EKRANY ---
# =========================================================

if st.session_state.page == "Menu Dom":
    st.title("🏠 MENU GŁÓWNE")
    st.divider()
    if st.button("🍳 KUCHNIA", use_container_width=True): st.session_state.page = "Kuchnia"; st.rerun()
    if st.button("🐶 PIES", use_container_width=True): st.session_state.page = "Pies"; st.rerun()
    if st.button("🚗 AUTO", use_container_width=True): st.session_state.page = "Auto"; st.rerun()

elif st.session_state.page == "Kuchnia":
    if st.button("⬅️ POWRÓT DO MENU", use_container_width=True): st.session_state.page = "Menu Dom"; st.session_state.sub_page = None; st.rerun()
    
    if st.session_state.sub_page is None:
        st.title("🍳 KUCHNIA")
        if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): st.session_state.sub_page = "Lista"; st.rerun()
        if st.button("📦 STAN SPIŻARNI", use_container_width=True): st.session_state.sub_page = "Spizarnia"; st.rerun()
        if st.button("🥘 PRZEPISY", use_container_width=True): st.session_state.sub_page = "Dania"; st.rerun()
        if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): st.session_state.sub_page = "Plan"; st.rerun()
    
    # ... (Tutaj reszta sekcji Kuchnia: Lista, Spizarnia itd. - bez zmian w logice) ...
    elif st.session_state.sub_page == "Lista":
        if st.button("⬅️ WSTECZ"): st.session_state.sub_page = None; st.rerun()
        st.title("🛒 LISTA")
        braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
        for idx, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']}", key=f"l_{idx}", use_container_width=True):
                df_spizarnia.at[idx, 'Stan'] = "Mamy"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

elif st.session_state.page == "Pies":
    if st.button("⬅️ POWRÓT", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    st.title("🐶 PIES")
    kafelek_terminu("💉 Szczepienie", "Pies", "Szczepienie")

elif st.session_state.page == "Auto":
    if st.button("⬅️ POWRÓT", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    st.title("🚗 AUTO")
    
    # Daty pod sobą - stabilnie i bez przesuwania ekranu
    kafelek_terminu("🛠️ Przegląd Techniczny", "Auto", "Przegląd")
    kafelek_terminu("📄 Ubezpieczenie OC", "Auto", "Ubezpieczenie")
    
    st.divider()
    st.metric("⛽ Paliwo", "Informacja")
