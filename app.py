import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Quiz Banca Dati", page_icon="📝", layout="centered")

st.title("📝 App Quiz Interattivo")

# Nome del file Excel caricato su GitHub (deve essere identico, anche nel maiuscolo/minuscolo)
nome_file_excel = "dog_progressioni_aree_26giu2026_banca_dati.xlsx"

@st.cache_data
def carica_dati(file_path):
    for skip in range(10):
        try:
            temp_df = pd.read_excel(file_path, skiprows=skip)
            temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
            possibili_nomi = ['QUESITO', 'DOMANDA', 'TESTO']
            trovata = [c for c in possibili_nomi if c in temp_df.columns]
            if trovata:
                col_quesito = trovata[0]
                temp_df = temp_df.dropna(subset=[col_quesito])
                return temp_df, col_quesito
        except Exception:
            continue
    return None, None

# Gestione dello stato del quiz
if "quiz_avviato" not in st.session_state:
    st.session_state.quiz_avviato = False
    st.session_state.df = None
    st.session_state.indice = 0
    st.session_state.punteggio = 0
    st.session_state.storico = []

# Caricamento automatico del file da GitHub
if not st.session_state.quiz_avviato:
    df, col_quesito = carica_dati(nome_file_excel)
    if df is not None:
        st.session_state.df = df.sample(frac=1).reset_index(drop=True)
        st.session_state.col_quesito = col_quesito
        st.session_state.quiz_avviato = True
        st.rerun()
    else:
        st.error(f"Impossibile leggere il file '{nome_file_excel}' o trovare la colonna delle domande. Assicurati che sia nella stessa cartella su GitHub.")

if st.session_state.quiz_avviato and st.session_state.df is not None:
    df = st.session_state.df
    indice = st.session_state.indice
    
    if indice < len(df):
        riga = df.iloc[indice]
        
        def trova_col(possibili):
            for p in possibili:
                for c in df.columns:
                    if p == c or p in c:
                        return c
            return None

        col_materia = trova_col(['MATERIA'])
        col_numero = trova_col(['NUMERO', 'N.'])
        col_giusta = trova_col(['RISPOSTA CORRETTA']) or trova_col(['CORRETTA'])
        col_errate = [c for c in df.columns if 'ERRATA' in c]

        materia = str(riga[col_materia]).strip().upper() if col_materia and pd.notna(riga[col_materia]) else "N/D"
        numero_orig = str(riga[col_numero]).replace('.0', '').strip() if col_numero and pd.notna(riga[col_numero]) else str(indice + 1)
        domanda = str(riga[st.session_state.col_quesito]).strip()
        risposta_giusta = str(riga[col_giusta]).strip() if col_giusta and pd.notna(riga[col_giusta]) else ""

        if "domanda_corrente" not in st.session_state or st.session_state.domanda_corrente != indice:
            errate_disp = [str(riga[ce]).strip() for ce in col_errate if pd.notna(riga[ce]) and str(riga[ce]).strip() != ""]
            err_1 = errate_disp[0] if len(errate_disp) > 0 else "Opzione errata 1"
            err_2 = errate_disp[1] if len(errate_disp) > 1 else "Opzione errata 2"

            opzioni = [risposta_giusta, err_1, err_2]
            opzioni = [o for o in opzioni if o]
            random.shuffle(opzioni)

            lettere = ['A', 'B', 'C'][:len(opzioni)]
            mappa = {lettere[i]: opzioni[i] for i in range(len(opzioni))}

            st.session_state.domanda_corrente = indice
            st.session_state.opzioni_mappa = mappa
            st.session_state.lettere_disponibili = lettere
            st.session_state.risposta_giusta = risposta_giusta
            st.session_state.domanda_testo = domanda
            st.session_state.materia = materia
            st.session_state.numero_orig = numero_orig

        st.markdown(f"### Domanda {indice + 1} di {len(df)}")
        st.caption(f"Materia: {st.session_state.materia} | Rif. n. {st.session_state.numero_orig}")
        st.markdown(f"**{st.session_state.domanda_testo}**")
        st.write("")

        with st.form(key=f"form_{indice}"):
            opzioni_radio = [f"{let}) {testo}" for let, testo in st.session_state.opzioni_mappa.items()]
            scelta_selezionata = st.radio("Seleziona la risposta:", opzioni_radio, key=f"scelta_{indice}")
            submitted = st.form_submit_button("Conferma Risposta")

        if submitted:
            lettera_scelta = scelta_selezionata.split(")")[0].strip()
            risposta_data_testo = st.session_state.opzioni_mappa[lettera_scelta]
            
            norm_data = " ".join(risposta_data_testo.split()).lower()
            norm_giusta = " ".join(st.session_state.risposta_giusta.split()).lower()

            if norm_data == norm_giusta:
                st.success("✔ ESATTO!")
                st.session_state.punteggio += 1
                esito = "ESATTO"
            else:
                st.error(f"✘ SBAGLIATO! La risposta corretta era:\n-> {st.session_state.risposta_giusta}")
                esito = "SBAGLIATO"

            st.session_state.storico.append({
                "Domanda": st.session_state.domanda_testo,
                "Tua Risposta": risposta_data_testo,
                "Risposta Corretta": st.session_state.risposta_giusta,
                "Esito": esito,
                "Materia": st.session_state.materia
            })

            st.session_state.indice += 1
            st.rerun()

    else:
        st.balloons()
        st.success(f"🎉 Quiz terminato! Punteggio finale: {st.session_state.punteggio} su {len(df)}")
        
        df_risultati = pd.DataFrame(st.session_state.storico)
        csv = df_risultati.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Scarica il report dei risultati (CSV)",
            data=csv,
            file_name=f"risultati_quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
        
        if st.button("Ricomincia Quiz"):
            st.session_state.quiz_avviato = False
            st.rerun()