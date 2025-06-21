import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import unicodedata

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

def remover_acentos(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', str(txt)) if unicodedata.category(c) != 'Mn')

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
tipo = categoria # leve / camionetes / pesada
df_filtrado = df[df["tipo_veiculo"] == tipo]

if termo_busca:
    termo_normalizado = remover_acentos(termo_busca.lower())

    df_filtrado = df_filtrado[df_filtrado["serviço"].apply(
        lambda x: termo_normalizado in remover_acentos(str(x).lower())
    )]



#st.data_editor(
#    df_filtrado.rename(columns={
#        "serviço": "Serviço",
#        "tempo_estimado": "⏱ Tempo Estimado",
#        "valor_base": "💰 Valor Base (R$)",
#        "valor_meio": "💰 Valor Meio (R$)",
#        "valor_max": "💰 Valor Maximo (R$)",
#        "tipo_veiculo": "Tipo de veiculo"
#    }),
#    column_config={
#        "Valor Base": st.column_config.NumberColumn(format="R$ %.2f"),
#        "Valor Médio": st.column_config.NumberColumn(format="R$ %.2f"),
#        "Valor Máximo": st.column_config.NumberColumn(format="R$ %.2f"),
#    },
#    use_container_width=True,
#    hide_index=True,
#    disabled=True
#)

#===========================================================================================================

# Converte o dataframe para HTML com classes personalizadas
tabela_html = df_filtrado.rename(columns={
    "serviço": "Serviço",
    "tempo_estimado": "Tempo",
    "valor_base": "Valor Base",
    "valor_meio": "Valor Médio",
    "valor_max": "Valor Máximo",
    "tipo_veiculo": "Tipo"
}).to_html(index=False, classes="tabela-centralizada", border=0, justify="center")

# CSS para centralizar
css = """
<style>
.tabela-centralizada {
    width: 100%;
    border-collapse: collapse;
    background-color: #111;
    color: white;
}

.tabela-centralizada th, .tabela-centralizada td {
    text-align: center;
    padding: 8px;
    border: 1px solid #444;
}
.tabela-centralizada th {
    background-color: #222;
    font-weight: bold;
    color: white;
}
</style>
"""

# Exibir tabela com CSS
st.markdown(css + tabela_html, unsafe_allow_html=True)
