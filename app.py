from datetime import datetime
import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Quiz Concorso", page_icon="📝", layout="centered")

st.title("📝 Quiz Interattivo - Preparazione Concorso")

# URL RAW del file Excel su GitHub
# Sostituisci "TuoNomeUtente", "TuoRepo", "main" e "data/banca_dati.xlsx" con i tuoi dati reali
url_github = "https://raw.githubusercontent.com/TuoNomeUtente/TuoRepo/main/data/banca_dati.xlsx"


@st.cache_data
def carica_dati_da_web(url):
  df = None
  colonna_quesito = None
  for skip in range(10):
    try:
      # pandas legge direttamente dall'URL web
      temp_df = pd.read_excel(url, skiprows=skip)
      temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
      possibili_nomi = ["QUESITO", "DOMANDA", "TESTO"]
      trovata = [c for c in possibili_nomi if c in temp_df.columns]
      if trovata:
        df = temp_df
        colonna_quesito = trovata[0]
        break
    except Exception:
      continue
  return df, colonna_quesito


# Caricamento automatico all'avvio dell'app
with st.spinner("Caricamento della banca dati in corso..."):
  df, colonna_quesito = carica_dati_da_web(url_github)