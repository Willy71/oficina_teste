import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from unidecode import unidecode

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

from unidecode import unidecode

# Filtros visuais
col1, col2 = st.columns([2, 3])
with col1:
    categoria = st.selectbox("🚗 Tipo de veículo", ["Mecânica leve", "Mecânica camionetes", "Mecânica pesada"])
with col2:
    # Criar lista de sugestões normalizadas
    servicos_lista = df["serviço"].dropna().unique().tolist()
    servicos_normalizados = {unidecode(s.lower()): s for s in servicos_lista}

    # Sugestões filtradas dinamicamente
    termo_digitado = st.text_input("🔍 Buscar serviço", placeholder="Ex: oleo, freio, revisao...").strip().lower()
    termo_digitado_norm = unidecode(termo_digitado)

    sugestoes = [v for k, v in servicos_normalizados.items() if termo_digitado_norm in k]
    sugestao_escolhida = st.selectbox("💡 Sugestões encontradas", options=[""] + sugestoes) if termo_digitado else ""


tipo = categoria
df_filtrado = df[df["tipo_veiculo"] == tipo]

if termo_digitado:
    df_filtrado = df_filtrado[df_filtrado["serviço"].apply(lambda x: termo_digitado_norm in unidecode(str(x).lower()))]
elif sugestao_escolhida:
    df_filtrado = df_filtrado[df_filtrado["serviço"] == sugestao_escolhida]



st.data_editor(
    df_filtrado.rename(columns={
        "serviço": "Serviço",
        "descrição": "Descrição",
        "tempo_estimado": "Tempo",
        "valor_base": "Valor Base",
        "valor_meio": "Valor Médio",
        "valor_max": "Valor Máximo",
        "tipo_veiculo": "Tipo"
    }),
    column_config={
        "Valor Base": st.column_config.NumberColumn(format="R$ %.2f"),
        "Valor Médio": st.column_config.NumberColumn(format="R$ %.2f"),
        "Valor Máximo": st.column_config.NumberColumn(format="R$ %.2f"),
    },
    use_container_width=True,
    hide_index=True,
    disabled=True
)


