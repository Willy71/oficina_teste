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
# Carrega a aba 'Hoja 30' com partes e peças
hoja30_df = pd.DataFrame(client.open_by_key(SPREADSHEET_KEY).worksheet("Hoja 30").get_all_records())

def remover_acentos(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', str(txt)) if unicodedata.category(c) != 'Mn')

# Carregar dados da planilha
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Filtros visuais
col1, col2 = st.columns([2, 3])
with col1:
    categoria = st.selectbox("🚗 Tipo de veículo", ["Mecânica leve", "Mecânica camionetes"])
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

# Converte o dataframe para HTML com classes personalizadas
tabela_html = df_filtrado.rename(columns={
    "serviço": "Serviço",
    "valor_base": "💰 Base",
    "valor_meio": "💰 Médio",
    "valor_max": "💰 Máximo",
    "tipo_veiculo": "Tipo"
}).to_html(index=False, classes="tabela-centralizada", border=0, justify="center")

# CSS para centralizar
css = """
<style>
.tabela-centralizada {
    width: 100%;
    border-collapse: collapse;
    background-color: #000;
    color: white;
}

.tabela-centralizada th, .tabela-centralizada td {
    text-align: center;
    padding: 6px;
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
st.text("")
st.subheader("💡 Ajude a melhorar a tabela")

st.markdown("""
Se você percebeu que algum serviço está faltando ou quer sugerir um valor mais justo para algum item, preencha o formulário abaixo.
Você pode também selecionar uma **Parte** e uma **Peça** do carro como referência.
""")

with st.form("sugestao_form"):
    nome_usuario = st.text_input("Seu nome (opcional)")
    servico_sugerido = st.text_input("🛠️ Serviço que deseja sugerir")
    valor_sugerido = st.text_input("💰 Valor sugerido (se aplicável)")
    
    col1, col2 = st.columns(2)
    with col1:
        parte = st.selectbox("🚗 Parte do veículo", sorted(hoja30_df["Partes"].dropna().unique()))
    with col2:
        peca = st.selectbox("🔩 Peça específica", sorted(hoja30_df["Peças"].dropna().unique()))
    
    comentario = st.text_area("🗣️ Comentário adicional")
    enviar = st.form_submit_button("📤 Enviar sugestão")

    if enviar:
        sugestao_sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("sugestoes")
        nova_linha = [nome_usuario, servico_sugerido, valor_sugerido, parte, peca, comentario]
        sugestao_sheet.append_row(nova_linha)
        st.success("Obrigado pela sua sugestão! Ela foi registrada com sucesso.")
