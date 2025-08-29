# 4_Painel_de_controle.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

#===================================================================================================================================================================
# Configuração de página (igual que tu código original)
st.set_page_config(
    page_title="Painel de controle",
    page_icon="📊",
    layout="wide"
)

#===================================================================================================================================================================
# Conexão com Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=SCOPES)
gc = gspread.authorize(creds)

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        worksheet = gc.open_by_key('1Wbfy1X3sVypDw-HTC4As0mHoq3a1jYDiPaO3x6YF4Vk').worksheet('Hoja 1')
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        # Conversão de datas
        df['date_in'] = pd.to_datetime(df['date_in'], dayfirst=True, errors='coerce')
        df['date_prev'] = pd.to_datetime(df['date_prev'], dayfirst=True, errors='coerce')
        df['date_out'] = pd.to_datetime(df['date_out'], dayfirst=True, errors='coerce')
        
        df_completo = df.copy()

        # Filtrar apenas veículos NÃO Entregados
        df_filtrado = df[~df['estado'].astype(str).str.strip().str.lower().eq('Entregado')]
        
        return df_filtrado.sort_values('date_in', ascending=False), df_completo
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

#===================================================================================================================================================
# Título e carregamento de dados
st.title("📊 Painel de Controle de Veículos")

#===================================================================================================================================================
# Carregando os dados corretamente
dados, dados_completos = carregar_dados()

# Normalizar a coluna 'estado'
dados_completos['estado'] = dados_completos['estado'].astype(str).str.strip().str.lower()

# Filtrar registros com estado "entregado"
entregados_df = dados_completos[dados_completos['estado'] == 'entregado']
entregues_total = entregados_df.shape[0]

# Obter o maior user_id (último ID)
ultimo_id = dados_completos['user_id'].max()

# ==============================
# 📌 NOVA LÓGICA: Veículos na Oficina
# ==============================
estados_na_oficina = [
    "entrada", 
    "em orçamento",
    "aguardando aprovação",
    "em reparação",
    "concluido"
]

na_oficina_df = dados_completos[dados_completos['estado'].isin(estados_na_oficina)]
veiculos_no_taller = na_oficina_df.shape[0]

# 📌 FILTRAR DADOS: excluir entregues da visualização
dados = dados[dados['estado'].astype(str).str.strip().str.lower() != 'entregado']

#===================================================================================================================================================
# 🔒 Checar si hay datos
if dados.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()
else:
    # Carregar dados e tratar datas
    dados, dados_completos = carregar_dados()
    dados['estado'] = dados['estado'].astype(str).str.strip()
    dados['date_in'] = pd.to_datetime(dados['date_in'], dayfirst=True, errors='coerce')
    dados = dados.dropna(subset=["date_in"])
    dados['date_in'] = dados['date_in'].dt.date  # remover hora
    
    # Filtros visuais
    st.markdown("## 🔍 Filtros")
    min_date, max_date = dados['date_in'].min(), dados['date_in'].max()
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("📅 Data inicial", value=min_date, min_value=min_date, max_value=max_date, key="painel_inicio")
    with col2:
        data_final = st.date_input("📅 Data final", value=max_date, min_value=data_inicial, max_value=max_date, key="painel_fim")
    
    estados = dados['estado'].value_counts().index.tolist()
    estado_opcoes = ["Todos"] + estados
    estado_selecionado = st.selectbox("🧾 Status do veículo", estado_opcoes)

    # Aplicar filtros
    dados_filtrados = dados[
        (dados['date_in'] >= data_inicial) & (dados['date_in'] <= data_final)
    ]
    
    if estado_selecionado != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados['estado'] == estado_selecionado]

    # Função para formatar datas
    def formatar_data(serie_data):
        return pd.to_datetime(serie_data, errors='coerce').dt.strftime('%d/%m/%Y').fillna('')

    # Métricas resumidas
    st.subheader("Visão Geral")
    metricas = [
        ("📋 Registros totais", len(dados_completos)),
        ("🏠 Na Oficina", veiculos_no_taller),
        ("⏳ Orçamento", len(dados[dados['estado'] == "Em orçamento"])),
        ("🛠️ Reparação", len(dados[dados['estado'] == "Em reparação"])),
        ("✅ Prontos", len(dados[dados['estado'] == "Concluido"])),
        ("📅 Hoje", len(dados[dados['date_in'] == datetime.today().date()]))
    ]
    
    cols = st.columns(len(metricas))
    for col, (titulo, valor) in zip(cols, metricas):
        col.metric(titulo, valor)

    # Abas por status
    tabs = st.tabs(["📋 Todos", "🏠 Na Oficina", "⏳ Orçamento", "🛠️ Reparação", "✅ Prontos", "🚫 Não Aprovados"])
    
    with tabs[0]:  # Todos
        dados_mostrar = dados_filtrados[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico', 'dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(dados_mostrar, hide_index=True, use_container_width=True)

    with tabs[1]:  # Na oficina
        na_oficina = dados_filtrados[dados_filtrados['estado'].str.lower().isin(estados_na_oficina)]
        dados_mostrar = na_oficina[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(dados_mostrar, hide_index=True, use_container_width=True)

    with tabs[2]:  # Orçamento
        orcamento = dados_filtrados[dados_filtrados['estado'] == "Em orçamento"]
        dados_mostrar = orcamento[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(dados_mostrar, hide_index=True, use_container_width=True)

    with tabs[3]:  # Reparação
        reparacao = dados_filtrados[dados_filtrados['estado'] == "Em reparação"]
        dados_mostrar = reparacao[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(dados_mostrar, hide_index=True, use_container_width=True)

    with tabs[4]:  # Prontos
        estados_prontos = ["concluido", "entregado", "entregado e cobrado"]
        prontos = dados_filtrados[dados_filtrados['estado'].str.lower().isin(estados_prontos)]
        dados_mostrar = prontos[['date_in', 'date_out', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        dados_mostrar['date_out'] = formatar_data(dados_mostrar['date_out'])
        st.dataframe(dados_mostrar, hide_index=True, use_container_width=True)

    with tabs[5]:  # Não Aprovados
        nao_aprovados = dados_filtrados[dados_filtrados['estado'].str.lower().str.strip() == "não aprovado"]
        dados_mostrar = nao_aprovados[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(dados_mostrar, hide_index=True, use_container_width=True)

    # Gráfico de distribuição
    st.subheader("Distribuição por Status")
    contagem_status = dados['estado'].value_counts()
    st.bar_chart(contagem_status)
