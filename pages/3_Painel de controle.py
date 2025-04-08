# 4_Painel_de_controle.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

#===================================================================================================================================================================
# Configuración de página (igual que tu código original)
st.set_page_config(
    page_title="Painel de controle",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS (copiados de tu código original)
reduce_space = """
<style type="text/css">
div[data-testid="stAppViewBlockContainer"]{
    padding-top:30px;
}
</style>
"""
st.markdown(reduce_space, unsafe_allow_html=True)

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-image: url("https://github.com/Willy71/oficina/blob/main/pictures/wallpaper%20black%20vintage.jpg?raw=true");
background-size: 180%;
background-position: top left;
background-repeat: repeat;
background-attachment: local;
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
st.markdown(page_bg_img, unsafe_allow_html=True)

#===================================================================================================================================================================

# Conexão com Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=SCOPES)
gc = gspread.authorize(creds)

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        worksheet = gc.open_by_key('1kiXS0qeiCpWcNpKI-jmbzVgiRKrxlec9t8YQLDaqwU4').worksheet('Hoja 1')
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
        return pd.DataFrame()

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

# Calcular veículos no taller
veiculos_no_taller = ultimo_id - entregues_total

# 📌 FILTRAR DADOS: excluir entregues da visualização
dados = dados[dados['estado'].astype(str).str.strip().str.lower() != 'entregado']


#===================================================================================================================================================

# 🔒 Checar si hay datos
if dados.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()
else:
    # Sidebar com filtros
    with st.sidebar:
        st.header("Filtros")
        # Excluir os veículos entregues da exibição
        dados = dados[dados['estado'].astype(str).str.strip().str.lower() != 'entregado']
        
        # Filtro por estado com contagem
        estados = dados['estado'].value_counts().index.tolist()
        estado_opcoes = ["Todos"] + estados
        estado_selecionado = st.selectbox(
            "Status do veículo",
            estado_opcoes,
            format_func=lambda x: f"{x} ({len(dados[dados['estado']==x])})" if x != 'Todos' else x
        )
        
        # Filtro por datas com formato brasileiro
        min_date, max_date = dados['date_in'].min().date(), dados['date_in'].max().date()
        faixa_data = st.date_input(
            "Período de entrada",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )


    # Aplicar filtros
    dados_filtrados = dados.copy()
    
    if estado_selecionado != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados['estado'] == estado_selecionado]
    
    if len(faixa_data) == 2:
        dados_filtrados = dados_filtrados[
            (dados_filtrados['date_in'].dt.date >= faixa_data[0]) & 
            (dados_filtrados['date_in'].dt.date <= faixa_data[1])
        ]


    # Função para formatar datas
    def formatar_data(serie_data):
        return serie_data.dt.strftime('%d/%m/%Y').replace('NaT', '')
    
    # Métricas resumidas
    st.subheader("Visão Geral")
    #veiculos_no_taller = len(dados)

    metricas = [
        ("📋 Registros totais", len(dados_completos)),
        ("🏠 Na Oficina", veiculos_no_taller),
        ("⏳ Orçamento", len(dados[dados['estado'] == "Em orçamento"])),
        ("🛠️ Reparação", len(dados[dados['estado'] == "Em reparação"])),
        ("✅ Prontos", len(dados[dados['estado'] == "Concluido"])),
        ("📅 Hoje", len(dados[dados['date_in'].dt.date == datetime.today().date()]))
    ]
    
    cols = st.columns(len(metricas))
    for col, (titulo, valor) in zip(cols, metricas):
        col.metric(titulo, valor)


    # Abas por status
    tabs = st.tabs(["📋 Todos", "🏠 Na Oficina", "⏳ Orçamento", "🛠️ Reparação", "✅ Prontos"])
    
    with tabs[0]:  # Todos
        dados_mostrar = dados_filtrados[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )

    with tabs[1]:  # Na oficina
        na_oficina = dados_filtrados[dados_filtrados['estado'].str.lower().str.strip() != 'entregado']
        dados_mostrar = na_oficina[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tabs[2]:  # Orçamento
        orcamento = dados_filtrados[dados_filtrados['estado'] == "Em orçamento"]
        dados_mostrar = orcamento[['date_in', 'placa', 'carro', 'modelo', 'dono_empresa', 'date_prev']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        dados_mostrar['date_prev'] = formatar_data(dados_mostrar['date_prev'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "dono_empresa": "Cliente",
                "date_prev": "Previsto (D/M/A)"
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tabs[3]:  # Reparação
        reparacao = dados_filtrados[dados_filtrados['estado'] == "Em reparação"]
        dados_mostrar = reparacao[['date_in', 'placa', 'carro', 'modelo', 'dono_empresa', 'date_prev']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        dados_mostrar['date_prev'] = formatar_data(dados_mostrar['date_prev'])
        st.dataframe(
            dados_mostrar,
            hide_index=True,
            use_container_width=True
        )
    
    with tabs[4]:  # Prontos
        prontos = dados_filtrados[dados_filtrados['estado'] == "Concluido"]
        dados_mostrar = prontos[['date_in', 'placa', 'carro', 'modelo', 'dono_empresa', 'date_out']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        dados_mostrar['date_out'] = formatar_data(dados_mostrar['date_out'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_out": "Conclusão (D/M/A)"
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Gráfico de distribuição
    st.subheader("Distribuição por Status")
    contagem_status = dados['estado'].value_counts()
    st.bar_chart(contagem_status)
