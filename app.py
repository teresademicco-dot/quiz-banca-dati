import streamlit as st
import pandas as pd
import random
from datetime import datetime
import io
import requests

st.set_page_config(page_title="Quiz Concorso", page_icon="📝", layout="centered")

st.title("📝 Quiz Interattivo - Preparazione Concorso")

# 1. LINK RAW DI GITHUB (Sostituisci con il tuo link reale)
GITHUB_URL_DOG = "https://raw.githubusercontent.com/TUO_UTENTE/TUA_REPO/main/dog.xlsx"

@st.cache_data(ttl=600)
def scarica_da_github(url):
    """Scarica e legge il file Excel tramite URL Raw di GitHub"""
    if "TUO_UTENTE" in url:
        return None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return io.BytesIO(response.content)
    except Exception:
        pass
    return None

def analizza_excel(file_source):
    """Cerca la colonna delle domande all'interno del file Excel"""
    if file_source is None:
        return None, "File non disponibile."
    
    for skip in range(10):
        try:
            # Riporta il puntatore all'inizio se è un BytesIO
            if hasattr(file_source, "seek"):
                file_source.seek(0)
                
            temp_df = pd.read_excel(file_source, skiprows=skip)
            temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
            
            possibili_nomi = ['QUESITO', 'DOMANDA', 'TESTO']
            trovata = [c for c in possibili_nomi if c in temp_df.columns]
            
            if trovata:
                return temp_df, trovata[0]
        except Exception:
            continue
            
    return None, "Impossibile trovare una colonna valida per le domande (es. 'DOMANDA', 'QUESITO', 'TESTO') nelle prime 10 righe."

# --- MODALITÀ DI CARICAMENTO CLOUD / ALTERNATIVA ---
df = None
colonna_quesito = None
errore_caricamento = ""

# Tentativo 1: Caricamento automatico da GitHub
with st.spinner("Connessione a GitHub e caricamento banca dati..."):
    file_buffer = scarica_da_github(GITHUB_URL_DOG)
    if file_buffer is not None:
        df, colonna_quesito = analizza_excel(file_buffer)

# Tentativo 2: Se GitHub fallisce o non è configurato, mostra l'uploader manuale di riserva
if df is None:
    st.warning("⚠️ Impossibile caricare automaticamente il file da GitHub. Puoi caricare il file `dog.xlsx` manualmente qui sotto:")
    file_caricato = st.file_uploader("Carica il file Excel (dog.xlsx)", type=["xlsx", "xls"])
    
    if file_caricato is not None:
        df, colonna_quesito = analizza_excel(file_caricato)
    else:
        errore_caricamento = "Inserisci un link GitHub valido oppure carica il file manualmente tramite il box sopra."

# Se il DataFrame è stato caricato con successo, avvia la logica del quiz
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

    # Rimuove le righe vuote basandosi sulla colonna del quesito
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
        st.success(f"Banca dati caricata con successo! Trovate **{len(df)}** domande.")
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

            # Form di selezione risposta
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

            # Feedback dopo la conferma
            if st.session_state.risposta_confermata:
                if st.session_state.is_corretto:
                    st.success("✔ ESATTO! Ottimo lavoro.")
                else:
                    st.error(f"✘ SBAGLIATO!\n\nLa risposta corretta era: **{risposta_giusta}**")
                
                if st.button("Prossima Domanda ➡️", type="primary"):
                    st.session_state.indice_domanda += 1
                    st.session_state.risposta_confermata = False
                    st.rerun()

        else:
            st.balloons()
            st.success(f"🎉 Quiz terminato! Punteggio finale: **{st.session_state.punteggio} / {totale}**")
            
            df_risultati = pd.DataFrame(st.session_state.storico)
            csv = df_risultati.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Scarica il report dei risultati in CSV",
                data=csv,
                file_name=f"risultati_quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.