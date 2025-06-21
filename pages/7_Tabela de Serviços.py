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
tipo = categoria # leve / camionetes / pesada
df_filtrado = df[df["tipo_veiculo"] == tipo]

if termo_busca:
    df_filtrado = df_filtrado[df_filtrado["serviço"].str.lower().str.contains(termo_busca)]


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


st.markdown("### 📑 Lista de serviços")

if df_filtrado.empty:
    st.warning("Nenhum serviço encontrado com os critérios selecionados.")
else:
    for _, row in df_filtrado.iterrows():
        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.subheader(f"🔧 {row['serviço']}")
                st.markdown(f"**📝 Descrição:** {row['descrição']}")
                st.markdown(f"**⏱ Tempo estimado:** {row['tempo_estimado']}")
            with col2:
                st.markdown(f"**💰 Valor base:** R$ {row['valor_base']:.2f}")
                st.markdown(f"**💰 Valor médio:** R$ {row['valor_meio']:.2f}")
                st.markdown(f"**💰 Valor máximo:** R$ {row['valor_max']:.2f}")
            with col3:
                st.markdown(f"**🚗 Tipo de veículo:** {row['tipo_veiculo']}")
                st.markdown(f"**🔢 Código do serviço:** {row['id']}")


if df_filtrado.empty:
    st.warning("Nenhum serviço encontrado com os critérios selecionados.")
