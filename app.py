import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Quiz Concorso", page_icon="📝", layout="centered")

st.title("📝 Quiz Interattivo - Preparazione Concorso")

# URL diretto al file raw su GitHub
GITHUB_URL = "https://raw.githubusercontent.com/teresademicco-dot/quiz-banca-dati/main/dog_progressioni_aree_26giu2026_banca_dati.xlsx"

# Scelta tra file locale (uploader) o file da GitHub
scelta_fonte = st.radio("Scegli la fonte della banca dati:", ["Carica file Excel (.xlsx)", "Usa banca dati da GitHub"])

uploaded_file = None
if scelta_fonte == "Carica file Excel (.xlsx)":
    uploaded_file = st.file_uploader("Carica il file Excel (.xlsx)", type=["xlsx"])
else:
    uploaded_file = GITHUB_URL

if uploaded_file is not None:
    @st.cache_data
    def carica_dati(file):
        df = None
        colonna_quesito = None
        for skip in range(10):
            try:
                temp_df = pd.read_excel(file, skiprows=skip)
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

    df, colonna_quesito = carica_dati(uploaded_file)

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
                risposta_giusta