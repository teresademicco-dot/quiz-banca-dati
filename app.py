import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Quiz Concorso", page_icon="📝", layout="centered")

st.title("📝 Quiz Interattivo - Preparazione Concorso")
st.write("Caricamento della banca dati direttamente da GitHub...")

# INSERISCI QUI IL TUO LINK RAW DI GITHUB DEL FILE "dog"
# Esempio: "https://raw.githubusercontent.com/tuo_utente/tua_repo/main/dog.xlsx"
GITHUB_URL_DOG = "https://raw.githubusercontent.com/TUO_UTENTE/TUA_REPO/main/dog.xlsx"

@st.cache_data
def carica_dati_da_github(url):
    df = None
    colonna_quesito = None
    for skip in range(10):
        try:
            temp_df = pd.read_excel(url, skiprows=skip)
            temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
            possibili_nomi = ['QUESITO', 'DOMANDA', 'TESTO']
            trovata = [c for c in possibili_nomi if c in temp_df.columns]
            if trovata:
                df = temp_df
                colonna_quesito = trovata[0]
                break
        except Exception:
            continue
    return df, colonna_quesito

# Caricamento automatico dal cloud
try:
    df, colonna_quesito = carica_dati_da_github(GITHUB_URL_DOG)
except Exception as e:
    df = None
    colonna_quesito = None

if df is not None:
    def trova_colonna(possibili):
        for p in possibili:
            for c in df.columns:
                if p == c or p in c:
                    return c
        return None

    col_materia = trova_colonna(['MATERIA'])
    col_numero = trova_colonna(['NUMERO', 'N.'])
    col_giusta = trova_colonna(['RISPOSTA CORRETTA'])
    if not col_giusta:
        col_giusta = trova_colonna(['CORRETTA'])
    col_errate = [c for c in df.columns if 'ERRATA' in c]

    df = df.dropna(subset=[colonna_quesito])

    # Inizializzazione dello stato della sessione
    if 'quiz_avviato' not in st.session_state:
        st.session_state.quiz_avviato = False
        st.session_state.indice_domanda = 0
        st.session_state.punteggio = 0
        st.session_state.storico = []
        st.session_state.opzioni_correnti = None
        st.session_state.risposta_data = None
        st.session_state.risposta_confermata = False
        st.session_state.is_corretto = False

    if not st.session_state.quiz_avviato:
        if st.button("🚀 Avvia / Mescola Quiz", type="primary"):
            st.session_state.df_shuffled = df.sample(frac=1).reset_index(drop=True)
            st.session_state.indice_domanda = 0
            st.session_state.punteggio = 0
            st.session_state.storico = []
            st.session_state.quiz_avviato = True
            st.session_state.opzioni_correnti = None
            st.session_state.risposta_confermata = False
            st.rerun()
    else:
        df_q = st.session_state.df_shuffled
        totale = len(df_q)
        idx = st.session_state.indice_domanda

        if idx < totale:
            riga = df_q.iloc[idx]
            materia = str(riga[col_materia]).strip().upper() if col_materia and pd.notna(riga[col_materia]) else "N/D"
            numero_orig = str(riga[col_numero]).replace('.0', '').strip() if col_numero and pd.notna(riga[col_numero]) else str(idx + 1)
            domanda = str(riga[colonna_quesito]).strip()
            risposta_giusta = str(riga[col_giusta]).strip() if col_giusta and pd.notna(riga[col_giusta]) else ""

            # Generazione opzioni casuali per la domanda corrente
            if st.session_state.opzioni_correnti is None or st.session_state.get('corrente_idx') != idx:
                errate_disponibili = []
                for ce in col_errate:
                    val = riga[ce]
                    if pd.notna(val) and str(val).strip() != "":
                        errate_disponibili.append(str(val).strip())
                
                if len(errate_disponibili) >= 2:
                    r_err1, r_err2 = errate_disponibili[0], errate_disponibili[1]
                elif len(errate_disponibili) == 1:
                    r_err1, r_err2 = errate_disponibili[0], "Altra opzione"
                else:
                    r_err1, r_err2 = "Opzione errata 1", "Opzione errata 2"

                opzioni = [risposta_giusta, r_err1, r_err2]
                opzioni = [o for o in opzioni if o]
                random.shuffle(opzioni)
                
                lettere = ['A', 'B', 'C'][:len(opzioni)]
                mappa = {lettere[i]: opzioni[i] for i in range(len(opzioni))}
                
                st.session_state.opzioni_correnti = opzioni
                st.session_state.lettere_correnti = lettere
                st.session_state.mappa_opzioni = mappa
                st.session_state.corrente_idx = idx
                st.session_state.risposta_data = None
                st.session_state.risposta_confermata = False

            st.markdown(f"### Domanda {idx + 1} di {totale}")
            st.caption(f"Materia: {materia} | Rif. n. {numero_orig}")
            st.markdown(f"**{domanda}**")

            # Se non ha ancora risposto, mostra il form di selezione
            if not st.session_state.risposta_confermata:
                with st.form(key=f"form_q_{idx}"):
                    scelta = st.radio(
                        "Seleziona la risposta:", 
                        options=st.session_state.lettere_correnti, 
                        format_func=lambda x: f"{x}) {st.session_state.mappa_opzioni[x]}"
                    )
                    submitted = st.form_submit_button("Conferma Risposta")

                if submitted:
                    st.session_state.risposta_data = scelta
                    risposta_testo = st.session_state.mappa_opzioni[scelta]
                    
                    norm_data = " ".join(risposta_testo.split()).lower()
                    norm_giusta = " ".join(risposta_giusta.split()).lower()

                    is_corretto = (norm_data == norm_giusta)
                    if is_corretto:
                        st.session_state.punteggio += 1
                        esito = "ESATTO"
                    else:
                        esito = "SBAGLIATO"

                    st.session_state.storico.append({
                        "Domanda": domanda,
                        "Tua Risposta": risposta_testo,
                        "Risposta Corretta": risposta_giusta,
                        "Esito": esito,
                        "Materia": materia
                    })
                    st.session_state.is_corretto = is_corretto
                    st.session_state.risposta_confermata = True
                    st.rerun()

            # Se ha già risposto, mostra il feedback colorato
            if st.session_state.risposta_confermata:
                if st.session_state.is_corretto:
                    st.success("✔ ESATTO! Ottimo lavoro.")
                else:
                    st.error