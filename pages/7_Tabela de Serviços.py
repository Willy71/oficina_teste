import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Tabela de Serviços", page_icon="🛠️", layout="wide")
st.title("📋 Tabela de Serviços")
st.caption("Consulte aqui os valores padrão de serviços para carros, camionetes e veículos pesados.")

# Conexão com Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_INFO = st.secrets["gsheets"]
SPREADSHEET_KEY = '1Wbfy1X3sVypDw-HTC4As0mHoq3a1jYDiPaO3x6YF4Vk' 
SHEET_NAME = "servicos"

credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

# Carregar dados da planilha
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Filtros visuais
col1, col2 = st.columns([2, 3])
with col1:
    categoria = st.selectbox("🚗 Tipo de veículo", ["Mecânica leve", "Mecânica camionetes", "Mecânica pesada"])
with col2:
    termo_busca = st.text_input("🔍 Buscar serviço pelo nome", placeholder="Ex: troca, freio, revisão...").strip().lower()

# Aplicar filtros
tipo = categoria.lower().split()[-1]  # leve / camionetes / pesada
df["tipo_veiculo"] = df["tipo_veiculo"].astype(str).str.lower().str.strip()
df_filtrado = df[df["tipo_veiculo"] == tipo]

if termo_busca:
    df_filtrado = df_filtrado[df_filtrado["servico"].str.lower().str.contains(termo_busca)]

# Exibir tabela
st.markdown("### 📑 Lista de serviços")
st.dataframe(
    df_filtrado[["serviço", "descrição", "tempo_estimado", "valor_base", "valor_meio", "valor_max", "tipo_veiculo"]]
    .rename(columns={
        "serviço": "Serviço",
        "descrição": "Descrição",
        "tempo_estimado": "⏱ Tempo Estimado",
        "valor_base": "💰 Valor Base (R$)",
        "valor_meio": "💰 Valor Meio (R$)",
        "valor_max": "💰 Valor Maximo (R$)",
        "tipo_veiculo": "Tipo de Veículo"
    })
    .sort_values("serviço"),
    use_container_width=True,
    hide_index=True
)

if df_filtrado.empty:
    st.warning("Nenhum serviço encontrado com os critérios selecionados.")
