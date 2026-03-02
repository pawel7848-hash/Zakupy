import streamlit as st

st.set_page_config(page_title="Inteligentny Dom", page_icon="🏠", layout="wide")

# --- INICJALIZACJA DANYCH (żeby nic nie znikało przy klikaniu) ---
if 'produkty_baza' not in st.session_state:
    # Tu wpisujemy rzeczy, które "zawsze" są w obiegu domowym
    st.session_state.produkty_baza = {
        "Papier toaletowy": True,
        "Mydło": True,
        "Chleb": True,
        "Masło": True,
        "Mleko": True,
        "Jajka": True,
        "Sól": True,
        "bagietka" True
    }

if 'zakupy' not in st.session_state:
    st.session_state.zakupy = []

# --- FUNKCJA AKTUALIZACJI LISTY ---
def aktualizuj_koszyk():
    # Czyścimy koszyk i dodajemy tylko to, co w spizarni jest "odznaczone" (False)
    nowy_koszyk = [produkt for produkt, jest_w_domu in st.session_state.produkty_baza.items() if not jest_w_domu]
    st.session_state.zakupy = nowy_koszyk

# --- MENU ---
zakladka = st.sidebar.radio("Menu", ["🛒 Koszyk", "📦 Spiżarnia / Zapasy", "🍲 Dania Obiadowe"])

# --- ZAKŁADKA: SPIŻARNIA (Tu zarządzasz co masz) ---
if zakladka == "📦 Spiżarnia / Zapasy":
    st.header("📦 Stan Spiżarni")
    st.info("Odznacz przedmiot, jeśli się kończy – trafi on automatycznie do Koszyka.")
    
    # Dodawanie nowej rzeczy do bazy domowej
    with st.expander("➕ Dodaj nowy przedmiot do bazy domowej"):
        nowy_p = st.text_input("Nazwa przedmiotu (np. Ręczniki papierowe):")
        if st.button("Dodaj do bazy"):
            if nowy_p:
                st.session_state.produkty_baza[nowy_p] = True
                st.rerun()

    st.write("---")
    
    # Lista przełączników
    for produkt in sorted(st.session_state.produkty_baza.keys()):
        # Wyświetlamy przełącznik (True = jest, False = brak)
        stan = st.toggle(f"{produkt}", value=st.session_state.produkty_baza[produkt], key=f"spiz_{produkt}")
        
        # Jeśli stan się zmienił w GUI, aktualizujemy bazę
        if stan != st.session_state.produkty_baza[produkt]:
            st.session_state.produkty_baza[produkt] = stan
            aktualizuj_koszyk()
            st.rerun()

# --- ZAKŁADKA: KOSZYK (To co w sklepie) ---
elif zakladka == "🛒 Koszyk":
    st.header("🛒 Lista zakupów")
    aktualizuj_koszyk() # Odśwież na wszelki wypadek
    
    if not st.session_state.zakupy:
        st.success("Wszystko masz w domu! Spiżarnia jest pełna.")
    else:
        st.warning(f"Brakuje Ci {len(st.session_state.zakupy)} rzeczy:")
        for i, produkt in enumerate(st.session_state.zakupy):
            col1, col2 = st.columns([4, 1])
            col1.write(f"⚠️ **{produkt}**")
            if col2.button("KUPIONE", key=f"buy_{i}"):
                # Jak klikniesz kupione, wraca do spizarni jako "jest"
                st.session_state.produkty_baza[produkt] = True
                aktualizuj_koszyk()
                st.rerun()

# --- ZAKŁADKA: OBIADY (Tu dodajemy brakujące składniki do koszyka) ---
elif zakladka == "🍲 Dania Obiadowe":
    st.header("🍲 Co dziś gotujemy?")
    
    PRZEPISY = {
        "Jajecznica": ["Jajka", "Chleb", "Masło", "Sól"],
        "Spaghetti": ["Makaron", "Mięso mielone", "Pomidory", "Ser"]
    }

    for danie, skladniki in PRZEPISY.items():
        if st.button(f"Sprawdź składniki na: {danie}", use_container_width=True):
            braki = []
            for s in skladniki:
                # Jeśli składnika nie ma w bazie lub jest odznaczony (False)
                if s not in st.session_state.produkty_baza or not st.session_state.produkty_baza.get(s):
                    st.session_state.produkty_baza[s] = False # Ustawiamy jako brak
                    braki.append(s)
            
            aktualizuj_koszyk()
            if braki:
                st.error(f"Brakuje Ci: {', '.join(braki)}. Dodano do koszyka!")
            else:
                st.success("Wszystkie składniki masz w domu!")