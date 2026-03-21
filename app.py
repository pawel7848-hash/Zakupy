import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dom", layout="centered")
st.markdown("<style>.block-container {padding-top: 3.5rem !important;}</style>", unsafe_allow_html=True)

# --- INICJALIZACJA STANU ---
if 'page' not in st.session_state: 
    st.session_state.page = "Menu Dom"
if 'sub_page' not in st.session_state: 
    st.session_state.sub_page = None
if 'wybrane_miejsce' not in st.session_state: 
    st.session_state.wybrane_miejsce = None
if 'todo_rok' not in st.session_state: 
    st.session_state.todo_rok = None
if 'todo_miesiac' not in st.session_state: 
    st.session_state.todo_miesiac = None

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def get_data(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name)
        data.columns = data.columns.str.strip()
        return data
    except: 
        return pd.DataFrame()

def refresh_all():
    st.cache_data.clear()
    st.rerun()

# --- ŁADOWANIE DANYCH ---
df_spizarnia = get_data("Spizarnia")
df_dania = get_data("Dania")
df_plan = get_data("Plan")
df_inne = get_data("Inne")
df_todo = get_data("Todo")

# --- FUNKCJE POMOCNICZE ---
def kafelek_terminu(label, kategoria, nazwa_klucza):
    global df_inne
    row = df_inne[(df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)]
    today = datetime.now().date()
    data_final = today
    kolor = "gray"
    if not row.empty:
        val = str(row.iloc[0]['Wartosc']).strip()
        try: 
            data_final = datetime.strptime(val[:10], '%Y-%m-%d').date()
        except:
            try: 
                data_final = datetime.strptime(val[:10], '%d.%m.%Y').date()
            except: 
                data_final = today
        kolor = "green" if data_final >= today else "red"
    
    with st.popover(f":{kolor}[{label}: {data_final.strftime('%d.%m.%Y')}]", use_container_width=True):
        st.write(f"Zmień datę: {label}")
        nowa = st.date_input("Data", value=data_final, format="DD.MM.YYYY", key=f"d_{kategoria}{nazwa_klucza}")
        if st.button("Zapisz", key=f"b{kategoria}_{nazwa_klucza}"):
            nowa_str = nowa.strftime('%Y-%m-%d')
            mask = (df_inne['Kategoria'] == kategoria) & (df_inne['Nazwa'] == nazwa_klucza)
            if not df_inne[mask].empty: 
                df_inne.loc[mask, 'Wartosc'] = nowa_str
            else:
                new_r = pd.DataFrame([{"Kategoria": kategoria, "Nazwa": nazwa_klucza, "Wartosc": nowa_str}])
                df_inne = pd.concat([df_inne, new_r], ignore_index=True)
            conn.update(worksheet="Inne", data=df_inne)
            refresh_all()

# --- MENU GŁÓWNE ---
if st.session_state.page == "Menu Dom":
    st.title("🏠 MENU GŁÓWNE")
    st.divider()
    if st.button("🍳 KUCHNIA", use_container_width=True): 
        st.session_state.page = "Kuchnia"; st.rerun()
    if st.button("🐶 PIES", use_container_width=True): 
        st.session_state.page = "Pies"; st.rerun()
    if st.button("🚗 AUTO", use_container_width=True): 
        st.session_state.page = "Auto"; st.rerun()
    if st.button("📝 TO DO", use_container_width=True): 
        st.session_state.page = "Todo"; st.rerun()

# --- SEKCJA KUCHNIA ---
elif st.session_state.page == "Kuchnia":
    if st.button("⬅️ POWRÓT DO DOMU", use_container_width=True):
        st.session_state.page = "Menu Dom"; st.session_state.sub_page = None; st.rerun()
    
    if st.session_state.sub_page is None:
        st.title("🍳 KUCHNIA")
        if st.button("🛒 LISTA ZAKUPÓW", use_container_width=True): 
            st.session_state.sub_page = "Lista"; st.rerun()
        if st.button("📦 STAN SPIŻARNI", use_container_width=True): 
            st.session_state.sub_page = "Spizarnia"; st.rerun()
        if st.button("🥘 PRZEPISY", use_container_width=True): 
            st.session_state.sub_page = "Dania"; st.rerun()
        if st.button("📅 PLAN POSIŁKÓW", use_container_width=True): 
            st.session_state.sub_page = "Plan"; st.rerun()

    elif st.session_state.sub_page == "Lista":
        if st.button("⬅️ WSTECZ", use_container_width=True): 
            st.session_state.sub_page = None; st.rerun()
        st.title("🛒 LISTA ZAKUPÓW")
        
        with st.expander("➕ DODAJ PRODUKT", expanded=False):
            with st.form("q_add_list"):
                lista_wszystkich = sorted(df_spizarnia['Produkt'].unique().tolist()) if not df_spizarnia.empty else []
                q_n = st.selectbox("Wybierz produkt:", [""] + lista_wszystkich)
                new_p_name = st.text_input("LUB wpisz nowy produkt:")
                ist_m = sorted(df_spizarnia['Miejsce'].unique()) if not df_spizarnia.empty else []
                c1, c2 = st.columns(2)
                with c1: wyb = st.selectbox("Miejsce:", ["+ NOWE"] + ist_m)
                with c2: n_m = st.text_input("Lub wpisz nowe miejsce:")
                
                if st.form_submit_button("DODAJ DO LISTY", use_container_width=True):
                    final_name = new_p_name if new_p_name else q_n
                    if final_name:
                        f_m = n_m if n_m else (wyb if wyb != "+ NOWE" else "Inne")
                        mask = df_spizarnia['Produkt'].str.lower() == final_name.lower()
                        if not df_spizarnia[mask].empty:
                            df_spizarnia.loc[mask, 'Stan'] = "Brak"
                            df_spizarnia.loc[mask, 'Miejsce'] = f_m
                        else:
                            nw = pd.DataFrame([{"Produkt": final_name, "Stan": "Brak", "Miejsce": f_m}])
                            df_spizarnia = pd.concat([df_spizarnia, nw], ignore_index=True)
                        conn.update(worksheet="Spizarnia", data=df_spizarnia)
                        refresh_all()
        
        st.divider()
        braki = df_spizarnia[df_spizarnia['Stan'] == "Brak"].dropna(subset=['Produkt'])
        if braki.empty:
            st.info("Lista jest pusta! 🟢")
        for idx, r in braki.iterrows():
            if st.button(f"🔴 {r['Produkt']} ({r['Miejsce']})", key=f"l_{idx}", use_container_width=True):
                df_spizarnia.at[idx, 'Stan'] = "Mamy"
                conn.update(worksheet="Spizarnia", data=df_spizarnia)
                refresh_all()

    elif st.session_state.sub_page == "Spizarnia":
        if st.session_state.wybrane_miejsce is None:
            if st.button("⬅️ WSTECZ", use_container_width=True): 
                st.session_state.sub_page = None; st.rerun()
            miejsca = sorted(df_spizarnia['Miejsce'].fillna('Inne').unique())
            for m in miejsca:
                produkty_m = df_spizarnia[df_spizarnia['Miejsce'] == m]
                stany = produkty_m['Stan'].values
                ik = "🔴" if "Brak" in stany else ("🟡" if "Sprawdź" in stany else "🟢")
                if st.button(f"{ik} {m.upper()}", key=f"f_{m}", use_container_width=True):
                    st.session_state.wybrane_miejsce = m; st.rerun()
        else:
            if st.button("⬅️ POWRÓT", use_container_width=True): 
                st.session_state.wybrane_miejsce = None; st.rerun()
            m = st.session_state.wybrane_miejsce
            st.subheader(f"Lokalizacja: {m}")
            for idx, r in df_spizarnia[df_spizarnia['Miejsce'] == m].iterrows():
                stan = r['Stan']
                ikona = "🟢" if stan == "Mamy" else ("🟡" if stan == "Sprawdź" else "🔴")
                with st.popover(f"{ikona} {r['Produkt']}", use_container_width=True):
                    st.write(f"Zmień stan: {r['Produkt']}")
                    c1, c2, c3 = st.columns(3)
                    if c1.button("🟢", key=f"m_{idx}", use_container_width=True):
                        df_spizarnia.at[idx, 'Stan'] = "Mamy"
                        conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
                    if c2.button("🟡", key=f"s_{idx}", use_container_width=True):
                        df_spizarnia.at[idx, 'Stan'] = "Sprawdź"
                        conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
                    if c3.button("🔴", key=f"b_{idx}", use_container_width=True):
                        df_spizarnia.at[idx, 'Stan'] = "Brak"
                        conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()

    elif st.session_state.sub_page == "Dania":
        if st.button("⬅️ WSTECZ", use_container_width=True): 
            st.session_state.sub_page = None; st.rerun()
        st.title("🥘 TWOJE PRZEPISY")
        with st.expander("➕ DODAJ NOWY PRZEPIS"):
            with st.form("a_d"):
                dn = st.text_input("Nazwa dania:")
                ds = st.text_area("Składniki (rozdzielaj przecinkami):")
                if st.form_submit_button("ZAPISZ NOWE DANIE", use_container_width=True):
                    if dn:
                        nw = pd.DataFrame([{"Nazwa": dn, "Skladniki": ds}])
                        df_dania = pd.concat([df_dania, nw], ignore_index=True)
                        conn.update(worksheet="Dania", data=df_dania); refresh_all()
        st.divider()
        for idx, d in df_dania.dropna(subset=['Nazwa']).iterrows():
            with st.expander(f"🍴 {str(d['Nazwa']).upper()}"):
                st.write(f"Składniki: {d['Skladniki']}")
                c1, c2 = st.columns(2)
                if c1.button("🗑️ USUŃ", key=f"del_d_{idx}", use_container_width=True):
                    df_dania = df_dania.drop(idx)
                    conn.update(worksheet="Dania", data=df_dania); refresh_all()
                with c2.popover("📝 EDYTUJ", use_container_width=True):
                    new_s = st.text_area("Popraw składniki:", value=d['Skladniki'], key=f"ed_s_{idx}")
                    if st.button("ZAPISZ ZMIANY", key=f"sav_d_{idx}"):
                        df_dania.at[idx, 'Skladniki'] = new_s
                        conn.update(worksheet="Dania", data=df_dania); refresh_all()

    elif st.session_state.sub_page == "Plan":
        if st.button("⬅️ WSTECZ", use_container_width=True): 
            st.session_state.sub_page = None; st.rerun()
        st.title("📅 PLAN POSIŁKÓW")
        dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        with st.expander("➕ DODAJ DANIE DO PLANU"):
            with st.form("f_plan_nowy"):
                d_wybor = st.selectbox("Wybierz dzień:", dni)
                lista_dan = sorted(df_dania['Nazwa'].dropna().unique().tolist()) if not df_dania.empty else []
                danie_wybor = st.selectbox("Szukaj dania (zacznij pisać):", [""] + lista_dan)
                if st.form_submit_button("DODAJ DO PLANU", use_container_width=True):
                    if danie_wybor:
                        nw_p = pd.DataFrame([{"Dzien": d_wybor, "Danie": danie_wybor}])
                        df_plan = pd.concat([df_plan, nw_p], ignore_index=True)
                        conn.update(worksheet="Plan", data=df_plan)
                        przepis = df_dania[df_dania['Nazwa'] == danie_wybor].iloc[0]
                        skladniki = [s.strip() for s in str(przepis['Skladniki']).split(',') if s.strip()]
                        for s in skladniki:
                            mask = df_spizarnia['Produkt'].str.lower() == s.lower()
                            if not df_spizarnia[mask].empty:
                                if df_spizarnia.loc[mask, 'Stan'].values[0] != "Mamy":
                                    df_spizarnia.loc[mask, 'Stan'] = "Brak"
                            else:
                                ns = pd.DataFrame([{"Produkt": s, "Stan": "Brak", "Miejsce": "Inne"}])
                                df_spizarnia = pd.concat([df_spizarnia, ns], ignore_index=True)
                        conn.update(worksheet="Spizarnia", data=df_spizarnia); refresh_all()
        st.divider()
        for d in dni:
            plan_dnia = df_plan[df_plan['Dzien'] == d]
            if not plan_dnia.empty:
                st.subheader(f"📅 {d}")
                for idx, p in plan_dnia.iterrows():
                    d_nazwa = p['Danie']
                    czy_mamy = True; braki = []
                    if d_nazwa in df_dania['Nazwa'].values:
                        przepis = df_dania[df_dania['Nazwa'] == d_nazwa].iloc[0]
                        skladniki_d = [s.strip() for s in str(przepis['Skladniki']).split(',') if s.strip()]
                        for s in skladniki_d:
                            m = (df_spizarnia['Produkt'].str.lower() == s.lower()) & (df_spizarnia['Stan'] == "Mamy")
                            if df_spizarnia[m].empty:
                                czy_mamy = False; braki.append(s)
                    c1, col2 = st.columns([4, 1])
                    with c1:
                        if czy_mamy: st.success(f"🟢 {d_nazwa}")
                        else: st.error(f"🔴 {d_nazwa} (Braki: {', '.join(braki)})")
                    if col2.button("❌", key=f"del_p_{idx}"):
                        if d_nazwa in df_dania['Nazwa'].values:
                            przepis = df_dania[df_dania['Nazwa'] == d_nazwa].iloc[0]
                            sk_spr = [s.strip() for s in str(przepis['Skladniki']).split(',') if s.strip()]
                            for s in sk_spr:
                                mask_s = df_spizarnia['Produkt'].str.lower() == s.lower()
                                if not df_spizarnia[mask_s].empty and df_spizarnia.loc[mask_s, 'Stan'].values[0] == "Mamy":
                                    df_spizarnia.loc[mask_s, 'Stan'] = "Sprawdź"
                        conn.update(worksheet="Spizarnia", data=df_spizarnia)
                        df_plan = df_plan.drop(idx); conn.update(worksheet="Plan", data=df_plan); refresh_all()

# --- SEKCJA PIES ---
elif st.session_state.page == "Pies":
    if st.button("⬅️ POWRÓT", use_container_width=True): 
        st.session_state.page = "Menu Dom"; st.rerun()
    kafelek_terminu("💉 Szczepienie", "Pies", "Szczepienie")

# --- SEKCJA AUTO ---
elif st.session_state.page == "Auto":
    if st.button("⬅️ POWRÓT", use_container_width=True): 
        st.session_state.page = "Menu Dom"; st.rerun()
    kafelek_terminu("🛠️ Przegląd", "Auto", "Przegląd")
    kafelek_terminu("📄 OC", "Auto", "Ubezpieczenie")

# --- SEKCJA TODO ---
elif st.session_state.page == "Todo":
    if st.button("⬅️ POWRÓT DO MENU", use_container_width=True): 
        st.session_state.page = "Menu Dom"; st.session_state.todo_rok = None; st.session_state.todo_miesiac = None; st.rerun()
    
    if st.session_state.todo_rok is None:
        st.title("📅 WYBIERZ ROK")
        for r in [2026, 2027, 2028]:
            if st.button(f"🗓️ {r}", use_container_width=True):
                st.session_state.todo_rok = r; st.rerun()
    
    elif st.session_state.todo_miesiac is None:
        if st.button("⬅️ ZMIEŃ ROK", use_container_width=True): 
            st.session_state.todo_rok = None; st.rerun()
        st.title(f"🗓️ ROK {st.session_state.todo_rok}")
        miesiace = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
        c = st.columns(2)
        for i, m in enumerate(miesiace):
            if c[i % 2].button(m, use_container_width=True):
                st.session_state.todo_miesiac = m; st.rerun()
    
    else:
        if st.button(f"⬅️ ZMIEŃ MIESIĄC ({st.session_state.todo_miesiac})", use_container_width=True): 
            st.session_state.todo_miesiac = None; st.rerun()
        st.title(f"📝 {st.session_state.todo_miesiac} {st.session_state.todo_rok}")
        
        with st.expander("➕ DODAJ ZADANIE"):
            with st.form("t_add"):
                d_t = st.number_input("Dzień:", 1, 31)
                z_t = st.text_input("Zadanie:")
                if st.form_submit_button("ZAPISZ", use_container_width=True):
                    if z_t:
                        nw = pd.DataFrame([{"Rok": st.session_state.todo_rok, "Miesiac": st.session_state.todo_miesiac, "Dzien": d_t, "Zadanie": z_t}])
                        df_todo = pd.concat([df_todo, nw], ignore_index=True)
                        conn.update(worksheet="Todo", data=df_todo); refresh_all()
        
        st.divider()
        z_m = df_todo[(df_todo['Rok'] == st.session_state.todo_rok) & (df_todo['Miesiac'] == st.session_state.todo_miesiac)].sort_values("Dzien")
        if z_m.empty:
            st.info("Brak zadań! ✨")
        for idx, r in z_m.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{int(r['Dzien'])}.** {r['Zadanie']}")
            if c2.button("✅", key=f"t_{idx}"):
                df_todo = df_todo.drop(idx)
                conn.update(worksheet="Todo", data=df_todo); refresh_all()
