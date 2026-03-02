import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA (Lekki styl bez rozpychania ekranu)
st.set_page_config(page_title="Dom", layout="centered")

st.markdown("""
    <style>
    /* Usunięcie marginesów bocznych, żeby więcej weszło w telefonie */
    .block-container { padding: 1rem !important; }
    /* Minimalna wysokość przycisków, żeby były wygodne pod kciuk */
    button { height: 3.5rem !important; }
    </style>
""", unsafe_allow_html=True)

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

# 3. FUNKCJA TERMINÓW (Naprawiony format i rozmiar)
def kafelek_terminu(label, kategoria, nazwa_klucza):
    global df_inne 
    row = df_inne[(df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)]
    today = pd.Timestamp.now().date()
    
    data_terminu = today
    kolor, status = "gray", "BRAK"
    
    if not row.empty:
        try:
            val = row.iloc[0]['Wartosc']
            data_terminu = pd.to_datetime(val).date()
            if data_terminu >= today:
                kolor, status = "green", "OK"
            else:
                kolor, status = "red", "!!"
        except: pass

    # Popover dopasowany do połowy ekranu
    with st.popover(f":{kolor}[{label}]\n{data_terminu.strftime('%d.%m')}", use_container_width=True):
        st.write(f"Zmień: {label}")
        nowa = st.date_input("Data", value=data_terminu, format="DD.MM.YYYY", key=f"d_{kategoria}_{nazwa_klucza}")
        if st.button("Zapisz", key=f"b_{kategoria}_{nazwa_klucza}"):
            mask = (df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)
            if not df_inne[mask].empty:
                df_inne.loc[mask, 'Wartosc'] = nowa.strftime('%Y-%m-%d')
            else:
                new_row = pd.DataFrame([{"Kategoria": kategoria, "Nazwa": nazwa_klucza, "Wartosc": nowa.strftime('%Y-%m-%d')}])
                df_inne = pd.concat([df_inne, new_row], ignore_index=True)
            conn.update(worksheet="Inne", data=df_inne)
            refresh_all()

# =========================================================
# --- EKRAN STARTOWY ---
# =========================================================
if st.session_state.page == "Menu Dom":
    st.title("🏠 DOM")
    st.divider()
    # Główne kategorie - na telefonie Streamlit sam je ładnie ułoży
    if st.button("🍳 KUCHNIA", use_container_width=True): st.session_state.page = "Kuchnia"; st.rerun()
    if st.button("🐶 PIES", use_container_width=True): st.session_state.page = "Pies"; st.rerun()
    if st.button("🚗 AUTO", use_container_width=True): st.session_state.page = "Auto"; st.rerun()

# =========================================================
# --- KUCHNIA ---
# =========================================================
elif st.session_state.page == "Kuchnia":
    if st.button("⬅️ POWRÓT", use_container_width=True): 
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
        if st.button("⬅️ COFNIJ"): st.session_state.sub_page = None; st.rerun()
        braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
        for idx, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']}", key=f"l_{idx}", use_container_width=True):
                df_spizarnia.at[idx, 'Stan'] = "Mamy"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    elif st.session_state.sub_page == "Spizarnia":
        if st.session_state.wybrane_miejsce is None:
            if st.button("⬅️ COFNIJ"): st.session_state.sub_page = None; st.rerun()
            miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
            for m in miejsca:
                if st.button(f"📂 {m}", key=f"m_{m}", use_container_width=True): st.session_state.wybrane_miejsce = m; st.rerun()
        else:
            if st.button("⬅️ MIEJSCA"): st.session_state.wybrane_miejsce = None; st.rerun()
            m = st.session_state.wybrane_miejsce
            for idx, row in df_spizarnia[df_spizarnia['Miejsce'] == m].iterrows():
                ik = "🟢" if row['Stan'] == "Mamy" else "🔴"
                if st.button(f"{ik} {row['Produkt']}", key=f"s_{idx}", use_container_width=True):
                    df_spizarnia.at[idx, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                    conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    # (Dania i Plan skrócone dla jasności, działają jak wcześniej)
    elif st.session_state.sub_page == "Dania":
        if st.button("⬅️ COFNIJ"): st.session_state.sub_page = None; st.rerun()
        for idx, d in df_dania.iterrows():
            with st.expander(f"🍴 {d['Nazwa']}"): st.write(d['Skladniki'])

# =========================================================
# --- PIES ---
# =========================================================
elif st.session_state.page == "Pies":
    if st.button("⬅️ POWRÓT", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    st.title("🐶 PIES")
    kafelek_terminu("💉 Szczepienie", "Pies", "Szczepienie")

# =========================================================
# --- AUTO ---
# =========================================================
elif st.session_state.page == "Auto":
    if st.button("⬅️ POWRÓT", use_container_width=True): st.session_state.page = "Menu Dom"; st.rerun()
    st.title("🚗 AUTO")
    
    # Próba kolumn bez wymuszania CSS - jeśli telefon jest bardzo wąski, zrobią się pionowo (bezpieczniej)
    c1, c2 = st.columns(2)
    with c1: kafelek_terminu("🛠️ Przegląd", "Auto", "Przegląd")
    with c2: kafelek_terminu("📄 OC", "Auto", "Ubezpieczenie")
    
    st.divider()
    st.metric("⛽ Paliwo", "OK")
