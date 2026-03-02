import streamlit as st

st.set_page_config(page_title="Inteligentny Dom", page_icon="🏠", layout="wide")

# --- 1. INICJALIZACJA DANYCH ---
if 'produkty_baza' not in st.session_state:
    # Tutaj masz swoją bazę. Pamiętaj: "Nazwa": True, (przecinek na końcu!)
    st.session_state.produkty_baza = {
        "Papier toaletowy": True,
        "Mydło": True,
        "Chleb": True,
        "Masło": True,
        "Mleko": True,
        "Jajka": True,
        "Sól": True,
        "bagietka": True,
        "pieprz": True,
        "Masło": True,
        "Ser": True,
    }

if 'zakupy' not in st.session_state:
    st.session_state.zakupy = []

# --- 2. FUNKCJA AKTUALIZACJI ---
def aktualizuj_koszyk():
    nowy_koszyk = [produkt for produkt, jest_w_domu in st.session_state.produkty_baza.items() if not jest_w_domu]
    st.session_state.zakupy = nowy_koszyk

# --- 3. MENU BOCZNE ---
zakladka = st.sidebar.radio("Menu", ["🛒 Koszyk", "📦 Spiżarnia", "🍲 Dania Obiadowe"])

# --- 4. ZAKŁADKA: SPIŻARNIA (Z PODZIAŁEM NA KATEGORIE) ---
if zakladka == "📦 Spiżarnia":
    st.header("📦 Stan Spiżarni")
    
    # Tu tworzymy zakładki na górze strony
    tab_szafka1, tab_szafka2, tab_lodówka, tab_dodaj = st.tabs([
        "🍎 Szafka nad zlewem",
        "🧼 Szafka na prawo od zlewu", 
        "Lodówka",  
        "➕ Dodaj Nowy"])

    with tab_szafka1:
        # Tutaj wpisz nazwy rzeczy, które mają być w tej zakładce
        produkty_szafka1 = ["Chleb", "Masło", "Mleko", "Jajka", "Sól", "bagietka", "pieprz"]
        for p in sorted(produkty_szafka1):
            if p in st.session_state.produkty_baza:
                stan = st.toggle(f"{p}", value=st.session_state.produkty_baza[p], key=f"spiz_{p}")
                if stan != st.session_state.produkty_baza[p]:
                    st.session_state.produkty_baza[p] = stan
                    aktualizuj_koszyk()
                    st.rerun()

    with tab_szafka2:
        # Tutaj wpisz nazwy rzeczy z chemii
        produkty_szafka2 = ["Papier toaletowy", "Mydło"]
        for p in sorted(produkty_szafka2):
            if p in st.session_state.produkty_baza:
                stan = st.toggle(f"{p}", value=st.session_state.produkty_baza[p], key=f"spiz_{p}")
                if stan != st.session_state.produkty_baza[p]:
                    st.session_state.produkty_baza[p] = stan
                    aktualizuj_koszyk()
                    st.rerun()
    with tab_lodówka:
        # Tutaj wpisz nazwy rzeczy z chemii
        produkty_lodówka = ["Masło", "Ser"]
        for p in sorted(produkty_lodówka):
            if p in st.session_state.produkty_baza:
                stan = st.toggle(f"{p}", value=st.session_state.produkty_baza[p], key=f"spiz_{p}")
                if stan != st.session_state.produkty_baza[p]:
                    st.session_state.produkty_baza[p] = stan
                    aktualizuj_koszyk()
                    st.rerun()

    with tab_dodaj:
        st.subheader("Dodaj nowy przedmiot do bazy")
        nowy_p = st.text_input("Nazwa przedmiotu:")
        if st.button("Dodaj"):
            if nowy_p:
                st.session_state.produkty_baza[nowy_p] = True
                st.success(f"Dodano {nowy_p}! Pojawi się na liście ogólnej.")
                st.rerun()

# --- 5. ZAKŁADKA: KOSZYK ---
elif zakladka == "🛒 Koszyk":
    st.header("🛒 Twoja lista zakupów")
    aktualizuj_koszyk()
    
    if not st.session_state.zakupy:
        st.success("Wszystko masz! Spiżarnia pełna.")
    else:
        for i, produkt in enumerate(st.session_state.zakupy):
            col1, col2 = st.columns([4, 1])
            col1.write(f"⚠️ **{produkt}**")
            if col2.button("KUPIONE", key=f"buy_{i}"):
                st.session_state.produkty_baza[produkt] = True
                aktualizuj_koszyk()
                st.rerun()

# --- 6. ZAKŁADKA: OBIADY ---
elif zakladka == "🍲 Dania Obiadowe":
    st.header("🍲 Co dziś gotujemy?")
    PRZEPISY = {
        "Jajecznica": ["Jajka", "Chleb", "Masło", "Sól"],
        "Spaghetti": ["Makaron", "Mięso mielone", "Pomidory", "Ser"]
    }
    for danie, skladniki in PRZEPISY.items():
        if st.button(f"Sprawdź: {danie}", use_container_width=True):
            braki = []
            for s in skladniki:
                if s not in st.session_state.produkty_baza or not st.session_state.produkty_baza.get(s):
                    st.session_state.produkty_baza[s] = False
                    braki.append(s)
            aktualizuj_koszyk()
            if braki:
                st.error(f"Dodano do koszyka: {', '.join(braki)}")
            else:
                st.success("Masz wszystko na ten obiad!")