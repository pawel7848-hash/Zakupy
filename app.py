import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. KONFIGURACJA
st.set_page_config(page_title="Zarządzanie Domem", layout="centered")

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
df_inne = get_data("Inne") # Nowa zakładka na Psa i Auto

def wroc_do_domu():
    st.session_state.page = "Menu Dom"
    st.session_state.sub_page = None
    st.rerun()

# =========================================================
# --- EKRAN STARTOWY: DOM ---
# =========================================================
if st.session_state.page == "Menu Dom":
    st.title("🏠 DOM")
    st.divider()
    
    col_k, col_p, col_a = st.columns(3)
    if col_k.button("🍳\nKUCHNIA", use_container_width=True):
        st.session_state.page = "Kuchnia"; st.rerun()
    if col_p.button("🐶\nPIES", use_container_width=True):
        st.session_state.page = "Pies"; st.rerun()
    if col_a.button("🚗\nAUTO", use_container_width=True):
        st.session_state.page = "Auto"; st.rerun()

# =========================================================
# --- KATEGORIA: KUCHNIA (Ten sam kod co wcześniej) ---
# =========================================================
elif st.session_state.page == "Kuchnia":
    if st.session_state.sub_page is None:
        if st.button("⬅️ WRÓĆ DO MENU DOM", use_container_width=True): wroc_do_domu()
        st.title("🍳 KUCHNIA")
        if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): st.session_state.sub_page = "Lista"; st.rerun()
        if st.button("📦 STAN SPIŻARNI", use_container_width=True): st.session_state.sub_page = "Spizarnia"; st.rerun()
        if st.button("🥘 PRZEPISY (DANIA)", use_container_width=True): st.session_state.sub_page = "Dania"; st.rerun()
        if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): st.session_state.sub_page = "Plan"; st.rerun()
    
    # ... (Tutaj wstaw sekcje Lista, Spizarnia, Dania, Plan z poprzedniego kodu)
    # Dla oszczędności miejsca w odpowiedzi pomijam środek Kuchni, bo się nie zmienił
    elif st.session_state.sub_page == "Lista":
        if st.button("⬅️ WRÓĆ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("🛒 DO KUPIENIA")
        braki = df_spizarnia[df_spizarnia['Stan'] != "Mamy"]
        for index, row in braki.iterrows():
            if st.button(f"🔴 {row['Produkt']}", key=f"k_{index}", use_container_width=True):
                df_spizarnia.at[index, 'Stan'] = "Mamy"; conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
    
    elif st.session_state.sub_page == "Spizarnia":
        if st.session_state.wybrane_miejsce is None:
            if st.button("⬅️ WRÓĆ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
            st.title("📦 MIEJSCA")
            miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
            for m in miejsca:
                if st.button(f"📂 {m.upper()}", key=f"m_{m}", use_container_width=True):
                    st.session_state.wybrane_miejsce = m; st.rerun()
        else:
            if st.button("⬅️ WRÓĆ DO MIEJSC", use_container_width=True): st.session_state.wybrane_miejsce = None; st.rerun()
            miejsce = st.session_state.wybrane_miejsce
            produkty = df_spizarnia[df_spizarnia['Miejsce'] == miejsce]
            for index, row in produkty.iterrows():
                ikona = "🟢" if row['Stan'] == "Mamy" else "🔴"
                if st.button(f"{ikona} {row['Produkt']}", key=f"s_{index}", use_container_width=True):
                    df_spizarnia.at[index, 'Stan'] = "Brak" if row['Stan'] == "Mamy" else "Mamy"
                    conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    elif st.session_state.sub_page == "Dania":
        if st.button("⬅️ WRÓĆ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("🥘 PRZEPISY")
        for idx, d in df_dania.iterrows():
            with st.expander(f"🍴 {d['Nazwa'].upper()}"): st.write(d['Skladniki'])

    elif st.session_state.sub_page == "Plan":
        if st.button("⬅️ WRÓĆ", use_container_width=True): st.session_state.sub_page = None; st.rerun()
        st.title("📅 PLAN")
        # (Logika planu z poprzedniego kodu...)

# =========================================================
# --- KATEGORIA: PIES ---
# =========================================================
elif st.session_state.page == "Pies":
    if st.button("⬅️ WRÓĆ DO DOMU", use_container_width=True): wroc_do_domu()
    st.title("🐶 STREFA PSA")
    
    # Pobieranie daty z tabeli 'Inne'
    row_szczepienie = df_inne[(df_inne['Kategoria'] == 'Pies') & (df_inne['Nazwa'] == 'Szczepienie')]
    data_szczep = row_szczepienie.iloc[0]['Wartosc'] if not row_szczepienie.empty else "Nie ustawiono"

    st.info(f"💉 Ostatnie szczepienie: **{data_szczep}**")
    
    with st.expander("📝 Edytuj dane psa"):
        nowa_data_psa = st.date_input("Data ostatniego szczepienia:", format="YYYY-MM-DD")
        if st.button("Zaktualizuj datę szczepienia"):
            # Aktualizacja w DataFrame
            mask = (df_inne['Kategoria'] == 'Pies') & (df_inne['Nazwa'] == 'Szczepienie')
            if not df_inne[mask].empty:
                df_inne.loc[mask, 'Wartosc'] = str(nowa_data_psa)
            else:
                new_row = pd.DataFrame([{"Kategoria": "Pies", "Nazwa": "Szczepienie", "Wartosc": str(nowa_data_psa)}])
                df_inne = pd.concat([df_inne, new_row], ignore_index=True)
            
            conn.update(worksheet="Inne", data=df_inne)
            st.success("Zmieniono datę!")
            refresh_all()

# =========================================================
# --- KATEGORIA: AUTO ---
# =========================================================
elif st.session_state.page == "Auto":
    if st.button("⬅️ WRÓĆ DO DOMU", use_container_width=True): wroc_do_domu()
    st.title("🚗 STREFA AUTO")
    
    # Pobieranie danych
    row_przeglad = df_inne[(df_inne['Kategoria'] == 'Auto') & (df_inne['Nazwa'] == 'Przegląd')]
    row_oc = df_inne[(df_inne['Kategoria'] == 'Auto') & (df_inne['Nazwa'] == 'Ubezpieczenie')]
    
    # Konwersja dat (pobieramy dzisiejszą datę)
    today = pd.Timestamp.now().date()

    def wyswietl_termin(label, row_data, kategoria, nazwa_klucza):
        if not row_data.empty:
            data_str = row_data.iloc[0]['Wartosc']
            try:
                data_terminu = pd.to_datetime(data_str).date()
                # LOGIKA KOLORÓW: Jeśli data jest w przyszłości = Zielony, jeśli przeszła = Czerwony
                if data_terminu >= today:
                    color = "green"
                    status = "AKTUALNE"
                else:
                    color = "red"
                    status = "PO TERMINIE!"
            except:
                data_terminu = today
                color = "gray"
                status = "BŁĄD DATY"
        else:
            data_terminu = today
            color = "gray"
            status = "BRAK DANYCH"

        # Klikalny kafelek (Popover)
        with st.popover(f":{color}[{label}: {data_terminu}] \n\n {status}", use_container_width=True):
            st.write(f"Zmień datę dla: {label}")
            nowa = st.date_input(f"Wybierz nową datę ({label})", value=data_terminu, key=f"date_{nazwa_klucza}")
            if st.button(f"Zapisz {label}", key=f"btn_{nazwa_klucza}"):
                mask = (df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)
                if not df_inne[mask].empty:
                    df_inne.loc[mask, 'Wartosc'] = str(nowa)
                else:
                    new_row = pd.DataFrame([{"Kategoria": kategoria, "Nazwa": nazwa_klucza, "Wartosc": str(nowa)}])
                    df_inne = pd.concat([df_inne, new_row], ignore_index=True)
                
                conn.update(worksheet="Inne", data=df_inne)
                st.success("Zapisano!")
                refresh_all()

    # Wyświetlenie sekcji
    st.subheader("📅 Terminy i ubezpieczenie")
    st.write("Kliknij w termin, aby go zmienić:")
    
    wyswietl_termin("🛠️ Przegląd", row_przeglad, "Auto", "Przegląd")
    wyswietl_termin("📄 Ubezpieczenie OC", row_oc, "Auto", "Ubezpieczenie")

    st.divider()
    st.metric("⛽ Paliwo", "75%") # Tu w przyszłości możemy dodać logikę tankowania
            conn.update(worksheet="Inne", data=df_inne)
            st.success(f"Zaktualizowano {typ}!")
            refresh_all()

