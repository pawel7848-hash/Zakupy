import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA I STYLE CSS
st.set_page_config(page_title="Mój Dom", layout="centered")

# Magiczny CSS, który wymusza kolumny obok siebie na telefonie i poprawia wygląd
st.markdown("""
    <style>
    /* Wymuszenie równego podziału kolumn na mobile */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        gap: 0.5rem !important;
    }
    /* Zapobieganie rozszerzaniu się strony na boki */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    /* Stylizacja przycisków w kolumnach */
    [data-testid="column"] button {
        width: 100% !important;
        padding: 0px !important;
    }
    /* Zmniejszenie czcionki na małych kafelkach */
    [data-testid="column"] button p {
        font-size: 12px !important;
    }
    /* Odstępy aplikacji */
    .block-container {
        padding: 2rem 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. INICJALIZACJA I POŁĄCZENIE
if 'page' not in st.session_state: st.session_state.page = "Menu Dom"
if 'sub_page' not in st.session_state: st.session_state.sub_page = None
if 'wybrane_miejsce' not in st.session_state: st.session_state.wybrane_miejsce = None

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def get_data(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name)
        data.columns = data.columns.str.strip()
        return data
    except: return pd.DataFrame()

def refresh_all():
    st.cache_data.clear()
    st.rerun()

# POBIERANIE DANYCH
df_spizarnia = get_data("Spizarnia")
df_dania = get_data("Dania")
df_plan = get_data("Plan")
df_inne = get_data("Inne")

# 3. FUNKCJE POMOCNICZE
def wroc_do_domu():
    st.session_state.page = "Menu Dom"
    st.session_state.sub_page = None
    st.rerun()

def kafelek_terminu(label, kategoria, nazwa_klucza):
    global df_inne 
    row = df_inne[(df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)]
    today = pd.Timestamp.now().date()
    
    if not row.empty:
        try:
            val = row.iloc[0]['Wartosc']
            # dayfirst=True zapobiega zamianie dnia z miesiącem
            data_terminu = pd.to_datetime(val, dayfirst=False).date() 
            if data_terminu >= today:
                kolor, status = "green", "✅ OK"
            else:
                kolor, status = "red", "🚨 TERMIN!"
        except:
            data_terminu, kolor, status = today, "gray", "BŁĄD"
    else:
        data_terminu, kolor, status = today, "gray", "BRAK"

    # Wyświetlanie kafelka (Popover) z polskim formatem daty na wierzchu
    with st.popover(f":{kolor}[{label}]\n\n**{data_terminu.strftime('%d.%m.%Y')}**", use_container_width=True):
        st.write(f"Zmień datę: {label}")
        nowa = st.date_input(f"Wybierz datę", value=data_terminu, format="DD.MM.YYYY", key=f"d_{kategoria}_{nazwa_klucza}")
        if st.button(f"Zapisz", key=f"b_{kategoria}_{nazwa_klucza}"):
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
    # Trzy kolumny obok siebie w menu głównym
    c1, c2, c3 = st.columns(3)
    if c1.button("🍳\nKUCH", use_container_width=True): st.session_state.page = "Kuchnia"; st.rerun()
    if c2.button("🐶\nPIES", use_container_width=True): st.session_state.page = "Pies"; st.rerun()
    if c3.button("🚗\nAUTO", use_container_width=True): st.session_state.page = "Auto"; st.rerun()

# =========================================================
# --- KUCHNIA ---
# =========================================================
elif st.session_state.page == "Kuchnia":
    if st.session_state.sub_page is None:
        if st.button("⬅️ MENU DOM", use_container_width=True): wroc_do_domu()
        st.title("🍳 KUCHNIA")
        if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): st.session_state.sub_page = "Lista"; st.rerun()
        if st.button("📦 STAN SPIŻARNI", use_container_width=True): st.session_state.sub_page = "Spizarnia"; st.rerun()
        if st.button("🥘 PRZEPISY", use_container_width=True): st.session_state.sub_page = "Dania"; st.rerun()
        if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): st.session_state.sub_page = "Plan"; st.rerun()
    
    elif st.session_state.sub_page == "Lista":
        if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("🛒 LISTA")
        braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
        for idx, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']} ({row['Miejsce']})", key=f"l_{idx}", use_container_width=True):
                df_spizarnia.at[idx, 'Stan'] = "Mamy"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    elif st.session_state.sub_page == "Spizarnia":
        if st.session_state.wybrane_miejsce is None:
            if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
            miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
            for m in miejsca:
                if st.button(f"📂 {m.upper()}", key=f"m_{m}", use_container_width=True): st.session_state.wybrane_miejsce = m; st.rerun()
        else:
            c1, c2 = st.columns(2)
            if c1.button("⬅️ MIEJSCA", use_container_width=True): st.session_state.wybrane_miejsce = None; st.rerun()
            if c2.button("🏠 KUCH", use_container_width=True): st.session_state.sub_page = None; st.rerun()
            miejsce = st.session_state.wybrane_miejsce
            st.subheader(f"📍 {miejsce}")
            with st.expander("➕ Dodaj produkt"):
                with st.form("add"):
                    n = st.text_input("Nazwa:")
                    if st.form_submit_button("Zapisz"):
                        if n:
                            new = pd.DataFrame([{"Produkt": n, "Stan": "Mamy", "Miejsce": miejsce}])
                            df_spizarnia = pd.concat([df_spizarnia, new], ignore_index=True)
                            conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
            for idx, row in df_spizarnia[df_spizarnia['Miejsce'] == miejsce].iterrows():
                ik = "🟢" if row['Stan'] == "Mamy" else "🔴"
                if st.button(f"{ik} {row['Produkt']}", key=f"s_{idx}", use_container_width=True):
                    df_spizarnia.at[idx, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                    conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    elif st.session_state.sub_page == "Dania":
        if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("🥘 PRZEPISY")
        t1, t2 = st.tabs(["Lista", "Dodaj"])
        with t2:
            with st.form("fd"):
                nazwa = st.text_input("Danie:")
                sklad = st.text_area("Składniki (po przecinku):")
                if st.form_submit_button("Zapisz"):
                    new = pd.DataFrame([{"Nazwa": nazwa, "Skladniki": sklad}])
                    df_dania = pd.concat([df_dania, new], ignore_index=True)
                    conn.update(worksheet="Dania", data=df_dania); refresh_all()
        with t1:
            for idx, d in df_dania.iterrows():
                with st.expander(f"🍴 {d['Nazwa'].upper()}"): st.write(d['Skladniki'])

    elif st.session_state.sub_page == "Plan":
        if st.button("⬅️ WSTECZ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("📅 PLAN")
        dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        with st.expander("➕ DODAJ POSIŁEK"):
            with st.form("fp"):
                d_wybr = st.selectbox("Dzień", dni)
                danie_wybr = st.selectbox("Danie", df_dania['Nazwa'].unique() if not df_dania.empty else ["Brak"])
                if st.form_submit_button("Dodaj"):
                    new_p = pd.DataFrame([{"Dzien": d_wybr, "Danie": danie_wybr}])
                    df_plan = pd.concat([df_plan, new_p], ignore_index=True); conn.update(worksheet="Plan", data=df_plan)
                    # Logika braków w spiżarni
                    p_info = df_dania[df_dania['Nazwa'] == danie_wybr].iloc[0]
                    for s in [s.strip() for s in str(p_info['Skladniki']).split(',')]:
                        if df_spizarnia[df_spizarnia['Produkt'].str.contains(s, case=False, na=False)].empty:
                            new_s = pd.DataFrame([{"Produkt": s, "Stan": "Brak", "Miejsce": "Inne"}])
                            df_spizarnia = pd.concat([df_spizarnia, new_s], ignore_index=True)
                        else:
                            df_spizarnia.loc[df_spizarnia['Produkt'].str.contains(s, case=False, na=False), 'Stan'] = "Brak"
                    conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
        for d in dni:
            p_dnia = df_plan[df_plan['Dzien'] == d]
            if not p_dnia.empty:
                st.subheader(d)
                for idx, p in p_dnia.iterrows():
                    d_inf = df_dania[df_dania['Nazwa'] == p['Danie']]
                    kropka = "🟢"
                    if not d_inf.empty:
                        for s in [s.strip() for s in str(d_inf.iloc[0]['Skladniki']).split(',')]:
                            if df_spizarnia[(df_spizarnia['Produkt'].str.contains(s, case=False, na=False)) & (df_spizarnia['Stan'] == "Mamy")].empty:
                                kropka = "🔴"; break
                    c1, c2 = st.columns([4,1])
                    c1.write(f"{kropka} {p['Danie']}")
                    if c2.button("❌", key=f"del_{idx}"):
                        df_plan = df_plan.drop(idx); conn.update(worksheet="Plan", data=df_plan); refresh_all()

# =========================================================
# --- PIES ---
# =========================================================
elif st.session_state.page == "Pies":
    if st.button("⬅️ MENU DOM", use_container_width=True): wroc_do_domu()
    st.title("🐶 PIES")
    kafelek_terminu("💉 Szczepienie", "Pies", "Szczepienie")
    st.divider()
    st.subheader("🦴 Szybkie akcje")
    if st.button("🥩 Nakarmiłem psa", use_container_width=True): st.balloons()
    if st.button("🌳 Spacer", use_container_width=True): st.success("🐾 Pies zadowolony!")

# =========================================================
# --- AUTO ---
# =========================================================
elif st.session_state.page == "Auto":
    if st.button("⬅️ MENU DOM", use_container_width=True): wroc_do_domu()
    st.title("🚗 AUTO")
    
    # Przegląd i OC obok siebie na telefonie dzięki CSS na górze
    col_przeglad, col_oc = st.columns(2)
    with col_przeglad: kafelek_terminu("🛠️ Przegląd", "Auto", "Przegląd")
    with col_oc: kafelek_terminu("📄 OC", "Auto", "Ubezpieczenie")
    
    st.divider()
    st.metric("⛽ Paliwo", "Ok")
