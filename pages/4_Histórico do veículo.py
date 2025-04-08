import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Config página
st.set_page_config(page_title="Histórico do Veículo", page_icon="📋", layout="wide")

# Colocar background azul muy oscuro
page_bg_color = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-color: #00001a;
}}

[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
}}

[data-testid="stToolbar"] {{
right: 2rem;
}}

[data-testid="stSidebar"] {{
background: rgba(0,0,0,0);
}}
</style>
"""
st.markdown(page_bg_color, unsafe_allow_html=True)


# Autenticación
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
    return pd.DataFrame(records) if records else pd.DataFrame()

# ------------------------------
st.markdown("<h2 style='color: gold;'>📋 Histórico de Veículo</h2>", unsafe_allow_html=True)
placa = st.text_input("Digite a placa do veículo").upper()

if placa:
    df = cargar_datos()
    historico = df[df["placa"] == placa]

    if historico.empty:
        st.warning("Nenhum histórico encontrado para essa placa.")
    else:
        historico = historico.sort_values(by="date_in")  # ordem crescente

        # Mostrar dados do veículo (baseado na visita mais antiga)
        dados_veiculo = historico.iloc[0]
        st.markdown(f"""
        <div style='background-color: #262730; padding: 20px; border-radius: 10px;'>
            <h4 style='color: gold;'>🚗 Dados do Veículo</h4>
            <p style='color: white;'>Placa: <strong>{dados_veiculo['placa']}</strong></p>
            <p style='color: white;'>Marca: {dados_veiculo['carro']} | Modelo: {dados_veiculo['modelo']}</p>
            <p style='color: white;'>Ano: {dados_veiculo['ano']} | Cor: {dados_veiculo['cor']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # Mostrar cada visita como un "card"
        for i, row in historico.iterrows():
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
                <h5 style='color: gold;'>🛠️ Visita em {row['date_in']} - Estado: {row['estado']}</h5>
            """, unsafe_allow_html=True)
            
            st.markdown("<h6 style='color: #00ffcc;'>🔧 Serviços: </h6>", unsafe_allow_html=True)
            for n in range(1, 13):
                desc = row.get(f'desc_ser_{n}')
                val = row.get(f'valor_serv_{n}')
                if desc and str(desc).strip():
                    st.markdown(f"<p style='color:white;'>• {desc} — <strong>R$ {val}</strong></p>", unsafe_allow_html=True)

            st.markdown("<h6 style='color: #00ffcc;'>🧩 Peças utilizadas:</h6>", unsafe_allow_html=True)
            for n in range(1, 17):
                desc = row.get(f'desc_peca_{n}')
                val = row.get(f'valor_total_peca_{n}')
                if desc and str(desc).strip() and val and float(val) > 0:
                    st.markdown(f"<p style='color:white;'>• {desc} — <strong>R$ {val}</strong></p>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
