import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Histórico do Veículo", page_icon="📋", layout="wide")

# Conexión a Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_INFO = st.secrets["gsheets"]
SPREADSHEET_KEY = '1Wbfy1X3sVypDw-HTC4As0mHoq3a1jYDiPaO3x6YF4Vk'
SHEET_NAME = 'Hoja 1'

credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(credentials)
worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

# Cargar datos
def cargar_datos():
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce').fillna(0).astype(int)
    return df

# UI
st.markdown("<h2 style='color: gold;'>🔍 Histórico de Veículos</h2>", unsafe_allow_html=True)
placa = st.text_input("Digite a placa do veículo").upper()

if placa:
    df = cargar_datos()
    historico = df[df["placa"] == placa]
    
    if historico.empty:
        st.warning("Nenhum histórico encontrado para essa placa.")
    else:
        historico = historico.sort_values(by="date_in", ascending=False)
        st.success(f"{len(historico)} visita(s) encontradas.")
        
        st.dataframe(historico[[
            'user_id', 'date_in', 'date_out', 'estado',
            'desc_ser_1', 'valor_serv_1',
            'desc_ser_2', 'valor_serv_2',
            'desc_ser_3', 'valor_serv_3',
            'total_serviço', 'total_costo_final'
        ]], use_container_width=True)
