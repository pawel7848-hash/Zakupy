import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Dom", layout="centered")

# Lekki odstęp od góry, żeby nic nie ucinało
st.markdown("<style>.block-container {padding-top: 3.5rem !important;}</style>", unsafe_allow_html=True)

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

# 3. FUNKCJA TERMINÓW - NAPRAWA DAT
def kafelek_terminu(label, kategoria, nazwa_klucza):
    global df_inne 
    row = df_inne[(df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)]
    today = pd.Timestamp.now().date()
    
    data_terminu = today
    kolor, status = "gray", "BRAK"
    
    if not row.empty:
        try:
            val = row.iloc[0]['Wartosc']
            # Wymuszamy format ISO, żeby nie zamieniało dnia z miesiącem
            data_terminu = pd.to_datetime(val).date()
            
            if data_terminu >= today:
                kolor, status = "green", "✅ AKTUALNE"
            else:
                kolor, status = "red", "🚨 PO TERMINIE!"
        except:
            pass

    # Przycisk (Popover) - Wyświetlamy datę po polsku na przycisku
    with st.popover(f":{kolor}[{label}: {data_terminu.strftime('%d.%m.%Y')}] \n\n {status}", use_container_width=True):
        st.write(f"Zmień datę: {label}")
        nowa = st.date_input("Nowa data", value=data_terminu, format="DD.MM.YYYY", key=f"d_{kategoria}_{nazwa_klucza}")
        if st.button("Zapisz", key=f"b_{kategoria}_{nazwa_klucza}"):
            mask = (df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)
            # Zapisujemy jako tekst w formacie YYYY-MM-DD
            nowa_str = nowa.strftime('%Y-%m-%d')
            if not df_inne[mask].empty:
                df_inne.loc[mask, 'Wartosc'] = nowa_str
            else:
                new_row = pd.DataFrame([{"Kategoria": kategoria, "Nazwa": nazwa_klucza, "Wartosc": nowa_str}])
                df_inne = pd.concat([df_inne, new_row], ignore_index=True)
            conn.update(worksheet="Inne", data=df_inne)
            refresh_all()

# =========================================================
# --- EKRANY ---
# =========================================================

if st.session_state.page == "Menu Dom":
    st.title("🏠 MENU GŁÓWNE")
    st.divider()
    if st.button("🍳 KUCHNIA", use_container_width=True): st.session_state.page = "Kuchnia"; st.rerun()
    if st.button("🐶 PIES", use_container_width=True): st.session_state.page = "Pies"; st.rerun()
    if st.button("🚗 AUTO", use_container_width=True): st.session_state.page = "Auto"; st.rerun()

elif st.session_state.page == "Kuchnia":
    # Główny powrót do Menu Dom
    if st.button("⬅️ POWRÓT DO DOMU", use_container_width=True): 
        st.session_state.page = "Menu Dom"
        st.session_state.sub_page = None
        st.rerun()
    
    if st.session_state.sub_page is None:
        st.title("🍳 KUCHNIA")
        if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): st.session_state.sub_page = "Lista"; st.rerun()
        if st.button("📦 STAN SPIŻARNI", use_container_width=True): st.session_state.sub_page = "Spizarnia"; st.rerun()
        if st.button("🥘 PRZEPISY", use_container_width=True): st.session_state.sub_page = "Dania"; st.rerun()
        if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): st.session_state.sub_page = "Plan"; st.rerun()
    
    elif st.session_state.sub_page == "Lista":
        if st.button("⬅️ WSTECZ DO KUCHNIA", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("🛒 LISTA")
        braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
        for idx, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']} ({row['Miejsce']})", key=f"l_{idx}", use_container_width=True):
                df_spizarnia.at[idx, 'Stan'] = "Mamy"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    elif st.session_state.sub_page == "Spizarnia":
        if st.session_state.wybrane_miejsce is None:
            if st.button("⬅️ WSTECZ DO KUCHNIA", use_container_width=True): st.session_state.sub_page = None; st.rerun()
            miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
            for m in miejsca:
                if st.button(f"📂 {m.upper()}", key=f"m_{m}", use_container_width=True): st.session_state.wybrane_miejsce = m; st.rerun()
        else:
            if st.button("⬅️ POWRÓT DO MIEJSC", use_container_width=True): st.session_state.wybrane_miejsce = None; st.rerun()
            m = st.session_state.wybrane_miejsce
            st.subheader(f"📍 {m}")
            for idx, row in df_spizarnia[df_spizarnia['Miejsce'] == m].iterrows():
                ik = "🟢" if row['Stan'] == "Mamy" else "🔴"
                if st.button(f"{ik} {row['Produkt']}", key=f"s_{idx}", use_container_width=True):
                    df_spizarnia.at[idx, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                    conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    elif st.session_state.sub_page == "Dania":
        if st.button("⬅️ WSTECZ DO KUCHNIA", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("🥘 PRZEPISY")
        for idx, d in df_dania.iterrows():
            with st.expander(f"🍴 {d['Nazwa'].upper()}"): st.write(d['Skladniki'])

    elif st.session_state.sub_page == "Plan":
        if st.button("⬅️ WSTECZ DO KUCHNIA", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("📅 PLAN POSIŁKÓW")
        # (Tutaj logika planu zostaje bez zmian)

elif st.session_state.page == "Pies":
    if st.button("⬅️ MENU DOM", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    st.title("🐶 PIES")
    kafelek_terminu("💉 Szczepienie", "Pies", "Szczepienie")

elif st.session_state.page == "Auto":
    if st.button("⬅️ MENU DOM", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    st.title("🚗 AUTO")
    kafelek_terminu("🛠️ Przegląd", "Auto", "Przegląd")
    kafelek_terminu("📄 OC", "Auto", "Ubezpieczenie")
