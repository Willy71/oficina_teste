import streamlit as st
import pandas as pd
import gspread
import uuid
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from calendar import monthrange
import calendar
import plotly.express as px  # <- ADICIONADO

# Conexão com Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_INFO = st.secrets["gsheets"]
SPREADSHEET_KEY = '1Wbfy1X3sVypDw-HTC4As0mHoq3a1jYDiPaO3x6YF4Vk' 
SHEET_NAME = "fluxo"

credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

def safe_float(valor):
    """Convierte cualquier valor a float de manera segura"""
    if pd.isna(valor) or valor in [None, '']:
        return 0.0
    
    if isinstance(valor, (int, float)):
        return float(valor)

    try:
        str_valor = str(valor).strip().replace('R$', '').replace('$', '').replace('"', '')
        
        # 🇧🇷 Caso: formato brasileiro "1.234,56"
        if '.' in str_valor and ',' in str_valor:
            str_valor = str_valor.replace('.', '').replace(',', '.')
        elif ',' in str_valor:  # "1234,56"
            str_valor = str_valor.replace(',', '.')
        # si tiene solo punto, ya está ok

        return float(str_valor)
    except Exception as e:
        print(f"Error convertiendo valor: '{valor}'. Error: {e}")
        return 0.0


# En la función cargar_dados():
def carregar_dados():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    if "data_pag" in df.columns:
        df["data_pag"] = pd.to_datetime(df["data_pag"], dayfirst=True, errors='coerce').dt.date
        df["data_pag"] = df["data_pag"].fillna(df["data"])  # Rellena vacíos con 'data'

    
    # Depuración: mostrar tipos de datos
    #print("Tipos de datos antes de conversión:", df.dtypes)
    
    if "valor" in df.columns:
        # Primero convertir a string para limpieza uniforme
        df["valor"] = df["valor"].astype(str)
        # Aplicar conversión segura
        df["valor"] = df["valor"].apply(safe_float)
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors='coerce').dt.date

    
    # Depuración: mostrar resultado
    #print("Valores convertidos:", df["valor"].head())
    return df

def obter_proximo_id(df):
    if df.empty or 'ids' not in df.columns:
        return 1
    try:
        return int(df['ids'].max()) + 1
    except:
        return 1

def adicionar_lancamento(status, data, data_pag, cliente, descricao, carro, placa, motivo, forma, valor):
    df = carregar_dados()
    novo_id = obter_proximo_id(df)

    # Formatear fechas al estilo brasileiro
    data_fmt = pd.to_datetime(data).strftime("%d/%m/%Y")
    #data_pag_fmt = pd.to_datetime(data_pag).strftime("%d/%m/%Y") if data_pag else ""
    data_pag_fmt = pd.to_datetime(data_pag if data_pag else data).strftime("%d/%m/%Y")


    nova_linha = [novo_id, data_fmt, data_pag_fmt, cliente, descricao, carro, placa, motivo, forma, valor, status]
    sheet.append_row(nova_linha)
    return novo_id

def atualizar_linha_por_id(id_alvo, novos_dados):
    df = carregar_dados()
    if id_alvo in df["ids"].values:
        linha = df[df["ids"] == id_alvo].index[0] + 2  # +2 por cabeçalho e índice 0-based
        for i, valor in enumerate(novos_dados):
            sheet.update_cell(linha, i + 1, valor)
        return True
    return False

def excluir_linha_por_id(id_alvo):
    df = carregar_dados()
    if id_alvo in df["ids"].values:
        linha = int(df[df["ids"] == id_alvo].index[0]) + 2  # Convertir a int nativo
        sheet.delete_rows(linha)
        return True
    return False

def safe_float(valor):
    """Conversión robusta a float para formatos brasileños"""
    if pd.isna(valor) or valor in [None, '', 'nan', 'NaN', 'N/A']:
        return 0.0
    
    # Si ya es numérico
    if isinstance(valor, (int, float)):
        return float(valor)
    
    try:
        # Limpieza inicial
        str_valor = str(valor).strip()
        str_valor = str_valor.replace('R$', '').replace('$', '').strip()
        
        # Caso especial: vacío después de limpiar
        if not str_valor:
            return 0.0
            
        # Detección automática de formato
        if '.' in str_valor and ',' in str_valor:
            # Formato 1.234,56 (europeo/brasileño)
            if str_valor.find('.') < str_valor.find(','):
                return float(str_valor.replace('.', '').replace(',', '.'))
            # Formato 1,234.56 (americano)
            else:
                return float(str_valor.replace(',', ''))
        elif ',' in str_valor:
            # Formato 1234,56
            return float(str_valor.replace(',', '.'))
        else:
            # Formato simple
            return float(str_valor)
    except Exception as e:
        st.error(f"Error convertiendo valor: '{valor}'. Error: {str(e)}")
        return 0.0
        
def formatar_valor(valor, padrao=""):
    """
    Formatea valores para visualización segura
    
    Args:
        valor: Valor a formatear (str, float, int, None)
        padrao: Valor por defecto si no se puede formatear (default: "")
    
    Returns:
        str: Valor formateado o string vacío si es nulo/inválido
    """
    if pd.isna(valor) or valor in [None, '']:
        return padrao
    try:
        return str(valor).strip()
    except:
        return padrao

def formatar_dos(valor):
    try:
        valor_float = float(valor)
        return f"{valor_float:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "0,00"


def formatar_real(valor, padrao="0,00"):
    """
    Formata valores para o padrão monetário brasileiro (R$ 0,00)
    """
    try:
        if pd.isna(valor) or valor in [None, '']:
            return f"R$ {padrao}"
        
        # Tenta converter para float mesmo que venha como string com vírgula
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".")
        
        valor_float = float(valor)
        return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"R$ {padrao}"

def normalize_status(status):
    """Normaliza los valores de status a 'entrada', 'saida' o 'pendente'"""
    if pd.isna(status):
        return "pendente"  # o el valor por defecto que prefieras
    
    status = str(status).strip().lower()
    
    # Mapeo exhaustivo de posibles variaciones
    if status in ['entrada', 'entradas', 'ingreso', 'ingresos', 'income', 'in']:
        return 'entrada'
    elif status in ['saida', 'saída', 'salida', 'gasto', 'gastos', 'out', 'expense']:
        return 'saida'
    elif status in ['pendente', 'pendientes', 'pending', 'pend']:
        return 'pendente'
    
    return status  # Mantener original si no coincide

# Interface
# Configuración de página (igual que tu código original)
st.set_page_config(
    page_title="💰 Fluxo de Caixa",
    page_icon="💰",
    layout="wide"
)
st.title("💰 Fluxo de Caixa")

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "➕ Novo Lançamento", 
    "📋 Lançamentos", 
    "🛠️ Editar / Remover", 
    "📊 Resumo Financeiro",
    "📈 Análise de Gastos",
    "🔍 Buscar Gastos"
])


with aba1:
    st.subheader("➕ Novo Registro")
     # Mostrar información principal en cards
    with st.container():
        cols = st.columns(3)
        with cols[0]:
            tipo = st.selectbox("Tipo", ["entrada", "saida", "pendente"])
        with cols[1]:
            data = st.date_input("Data do lançamento")
        with cols[2]:    
            data_pag = st.date_input("Data de pagamento prevista", value=None) if tipo == "pendente" else None
    with st.container():
        cols = st.columns(3)
        with cols[1]:
            cliente = st.text_input("Cliente")
    descricao = st.text_input("Descrição")
    with st.container():
        cols = st.columns(4)
        with cols[1]:
            carro = st.text_input("Carro")
        with cols[2]:
            placa = st.text_input("Placa")
      
    motivo = st.text_input("Fornecedor")
    with st.container():
        cols = st.columns(4)
        with cols[1]:
            forma = st.selectbox("Forma de pagamento", ["dinheiro", "pix", "cartão", "boleto", "outro"])
        with cols[2]:
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    with st.container():
        cols = st.columns([3,2,2])
        with cols[1]:
            if st.button("Salvar Registro"):
                adicionar_lancamento(tipo, data, data_pag, cliente, descricao, carro, placa, motivo, forma, valor)
                st.success("Registro salvo com sucesso!")
                # 👇 Forzar recarga
                st.rerun()

with aba2:
    st.subheader("📋 Lançamentos")

    df = carregar_dados()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["data"])
    df["data"] = df["data"].dt.date  # Apenas data, sem hora

    st.markdown("### 📋 Filtrar lançamentos por tipo")

    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([3.5,0.5,3.5,0.5,3.5,0.5,3.5,1,1,1])
    mostrar_tipo = None
    with col1:
        if st.button("🟢 Entradas", key="btn_lan_entradas", use_container_width=True):
            mostrar_tipo = "entrada"
    with col3:
        if st.button("🔴 Saídas", key="btn_lan_saidas", use_container_width=True):
            mostrar_tipo = "saida"
    with col5:
        if st.button("🟡 Pendentes", key="btn_lan_pendentes", use_container_width=True):
            mostrar_tipo = "pendente"
    with col7:
        if st.button("📋 Todos", key="btn_lan_todos", use_container_width=True):
            mostrar_tipo = "todos"


    if mostrar_tipo:
        if mostrar_tipo == "todos":
            df_tipo = df
            st.markdown("#### 📋 Todos os lançamentos")
        else:
            df_tipo = df[df["status"] == mostrar_tipo]
            cor = {"entrada": "🟢", "saida": "🔴", "pendente": "🟡"}[mostrar_tipo]
            titulo = {"entrada": "Entradas", "saida": "Saídas", "pendente": "Pendentes"}[mostrar_tipo]
            st.markdown(f"#### {cor} {titulo}")
    
        st.dataframe(df_tipo.sort_values("data", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Selecione um tipo de lançamento para exibir os dados.")



with aba3:
    st.subheader("🛠️ Editar ou Remover Lançamento por ID")

    df = carregar_dados()
    df["ids"] = df["ids"].astype(int)  # Asegurar tipo entero

    if df.empty:
        st.info("Nenhum lançamento encontrado.")
    else:
        ids_disponiveis = df["ids"].sort_values(ascending=False).tolist()
        id_escolhido = st.selectbox("Selecione o ID do lançamento", ids_disponiveis)

        lancamento = df[df["ids"] == id_escolhido].iloc[0]

        with st.form("form_edicao_id"):
            nova_data = st.date_input("Data", pd.to_datetime(lancamento["data"], dayfirst=True))
            try:
                data_pag_padrao = pd.to_datetime(lancamento["data_pag"], dayfirst=True)
                if pd.isnull(data_pag_padrao):
                    data_pag_padrao = datetime.today()
            except Exception:
                data_pag_padrao = datetime.today()

            nova_data_pag = st.date_input("Data Pagamento (se aplicável)", data_pag_padrao)
            novo_cliente = st.text_input("Cliente", lancamento["cliente"])
            nova_descricao = st.text_input("Descrição", lancamento["descricao"])
            novo_carro = st.text_input("Carro", lancamento["carro"])
            nova_placa = st.text_input("Placa", lancamento["placa"])
            novo_motivo = st.text_input("Motivo", lancamento["motivo"])

            opcoes_forma = ["dinheiro", "pix", "cartão", "boleto", "outro"]
            valor_atual_forma = str(lancamento["form"]).strip().lower()
            idx_forma = opcoes_forma.index(valor_atual_forma) if valor_atual_forma in opcoes_forma else 0
            nova_forma = st.selectbox("Forma de Pagamento", opcoes_forma, index=idx_forma)

            try:
                valor_padrao = float(str(lancamento["valor"]).replace("R$", "").replace(",", ".").strip())
            except:
                valor_padrao = 0.0
            novo_valor = st.number_input("Valor", value=valor_padrao)

            status_opcoes = ["entrada", "saida", "pendente"]
            idx_status = status_opcoes.index(str(lancamento["status"]).strip().lower()) if lancamento["status"] in status_opcoes else 0
            novo_status = st.selectbox("Status", status_opcoes, index=idx_status)

            col1, col2 = st.columns(2)
            with col1:
                editar = st.form_submit_button("💾 Salvar Alterações")
            with col2:
                excluir = st.form_submit_button("🗑️ Remover")

        if editar:
            novos_dados = [
                id_escolhido,
                nova_data.strftime("%d/%m/%Y"),
                nova_data_pag.strftime("%d/%m/%Y"),
                novo_cliente,
                nova_descricao,
                novo_carro,
                nova_placa,
                novo_motivo,
                nova_forma,
                novo_valor,
                novo_status
            ]
            atualizado = atualizar_linha_por_id(id_escolhido, novos_dados)
            if atualizado:
                st.success("Lançamento atualizado com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao atualizar lançamento.")

        if excluir:
            removido = excluir_linha_por_id(id_escolhido)
            if removido:
                st.success(f"Lançamento com ID {id_escolhido} removido com sucesso!")
                st.rerun()
            else:
                st.warning("Erro ao remover lançamento.")

with aba4:
    st.subheader("📊 Resumo Financeiro")

    df = carregar_dados()

    # Limpieza robusta de datas
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["valor"] = df["valor"].apply(safe_float)

    # --- INICIO DA CORREÇÃO ---
    # 1. Converter para datetime64, que suporta o acessor .dt
    df["data_pag"] = pd.to_datetime(df["data_pag"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["data_pag"])
    
    if df.empty:
        st.warning("Não há dados com datas válidas para exibir o resumo.")
    else:
        # 2. AGORA que é datetime64, usar .dt para extrair o ano de forma segura
        anos_disponiveis = sorted(df['data_pag'].dt.year.unique(), reverse=True)
        if not anos_disponiveis:
            anos_disponiveis = [date.today().year]
        
        # Obter os limites de data DEPOIS de filtrar o dataframe
        data_min = df["data_pag"].min().date()
        data_max = df["data_pag"].max().date()

        st.caption(f"📅 Datas disponíveis: de {data_min.strftime('%d/%m/%Y')} até {data_max.strftime('%d/%m/%Y')}")

        col_mes, col_ano = st.columns(2)
        meses = {
            0: "Ano Inteiro", 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        mes_selecionado = col_mes.selectbox("Mês", options=list(meses.keys()), format_func=lambda x: meses[x], index=0)
        
        ano_selecionado = col_ano.selectbox("Ano", options=anos_disponiveis, index=0)
        
        # --- BLOCO GRÁFICO (sem alterações) ---
        st.markdown(f"### 📈 Lucro Mensal de {ano_selecionado}")
        
        df_ano = df[df['data_pag'].dt.year == ano_selecionado].copy()
        lucro_mensal = []
        
        meses_pt = [meses[i] for i in range(1, 13)]

        for mes_num, nome_mes in enumerate(meses_pt, 1):
            df_mes = df_ano[df_ano['data_pag'].dt.month == mes_num]
            
            entrada_mes = df_mes[df_mes["status"] == "entrada"]["valor"].sum()
            saida_mes = df_mes[df_mes["status"] == "saida"]["valor"].sum()
            lucro = entrada_mes - saida_mes
            
            lucro_mensal.append({"Mês": nome_mes, "Lucro": lucro})

        df_lucro_anual = pd.DataFrame(lucro_mensal)

        fig = px.bar(
            df_lucro_anual, x='Mês', y='Lucro', text='Lucro', title=f"Lucro por Mês em {ano_selecionado}"
        )
        fig.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
        fig.update_layout(xaxis_title="Mês", yaxis_title="Lucro (R$)", uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig, use_container_width=True)
        # --- FIM DO BLOCO GRÁFICO ---

        # 3. Converter para objetos 'date' para a lógica de filtragem com st.date_input
        df["data_pag"] = df["data_pag"].dt.date
        # --- FIM DA CORREÇÃO ---

        st.markdown("---")
        st.markdown(f"### 🗓️ Resumo para o período selecionado")
        
        if mes_selecionado != 0:
            primeiro_dia = date(ano_selecionado, mes_selecionado, 1)
            ultimo_dia = date(ano_selecionado, mes_selecionado, monthrange(ano_selecionado, mes_selecionado)[1])
        else:
            primeiro_dia = date(ano_selecionado, 1, 1)
            ultimo_dia = date(ano_selecionado, 12, 31)

        col1_data, col2_data = st.columns(2)
        data_inicio = col1_data.date_input("Data início", value=primeiro_dia, min_value=data_min, max_value=data_max)
        data_fim = col2_data.date_input("Data fim", value=ultimo_dia, min_value=data_min, max_value=data_max)

        df_filtrado = df[(df["data_pag"] >= data_inicio) & (df["data_pag"] <= data_fim)]

        total_entrada = df_filtrado[df_filtrado["status"] == "entrada"]["valor"].sum()
        total_saida = df_filtrado[df_filtrado["status"] == "saida"]["valor"].sum()
        total_pendente = df_filtrado[df_filtrado["status"] == "pendente"]["valor"].sum()
        saldo = total_entrada - total_saida
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🟢 Entradas", formatar_real(total_entrada))
        col2.metric("🔴 Saídas", formatar_real(total_saida))
        col3.metric("🟡 Pendentes", formatar_real(total_pendente))
        col4.metric("💰 Saldo", formatar_real(saldo))

        st.markdown("---")
        st.markdown("### 📋 Lançamentos do Período")

        col1_btn, _, col2_btn, _, col3_btn, _, col4_btn = st.columns([2, 0.2, 2, 0.2, 2, 0.2, 2])
        mostrar_tipo_detalhe = st.session_state.get('mostrar_tipo_detalhe', 'todos')
        
        if col1_btn.button("🟢 Entradas", key="btn_resumo_entradas", use_container_width=True):
            mostrar_tipo_detalhe = "entrada"
        if col2_btn.button("🔴 Saídas", key="btn_resumo_saidas", use_container_width=True):
            mostrar_tipo_detalhe = "saida"
        if col3_btn.button("🟡 Pendentes", key="btn_resumo_pendentes", use_container_width=True):
            mostrar_tipo_detalhe = "pendente"
        if col4_btn.button("📋 Todos", key="btn_resumo_todos", use_container_width=True):
            mostrar_tipo_detalhe = "todos"
        
        st.session_state.mostrar_tipo_detalhe = mostrar_tipo_detalhe
        
        if mostrar_tipo_detalhe:
            if mostrar_tipo_detalhe == "todos":
                df_tipo = df_filtrado
                st.markdown("#### 📋 Todos os lançamentos no período")
            else:
                df_tipo = df_filtrado[df_filtrado["status"] == mostrar_tipo_detalhe]
                cor = {"entrada": "🟢", "saida": "🔴", "pendente": "🟡"}[mostrar_tipo_detalhe]
                titulo_map = {"entrada": "Entradas", "saida": "Saídas", "pendente": "Pendentes"}
                st.markdown(f"#### {cor} {titulo_map[mostrar_tipo_detalhe]} no período")
                
            st.dataframe(df_tipo.sort_values("data_pag", ascending=False), use_container_width=True, hide_index=True)


with aba5:
    st.subheader("📈 Análise de Gastos por Fornecedor")

    df = carregar_dados()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["valor"] = df["valor"].apply(safe_float)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["data"])
    df["data"] = df["data"].dt.date  # Remueve hora

    df_gastos = df[df["status"] == "saida"]

    if df_gastos.empty:
        st.warning("Não há registros de saída para análise.")
    else:
        data_min = df_gastos["data"].min()
        data_max = df_gastos["data"].max()

        st.caption(f"📅 Gastos registrados entre {data_min.strftime('%d/%m/%Y')} e {data_max.strftime('%d/%m/%Y')}")

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input(
                "Data início (gastos)",
                value=data_min,
                min_value=data_min,
                max_value=data_max,
                key="inicio_gasto"
            )
        with col2:
            data_fim = st.date_input(
                "Data fim (gastos)",
                value=data_max,
                min_value=data_inicio,
                max_value=data_max,
                key="fim_gasto"
            )

        df_filtrado = df_gastos[(df_gastos["data"] >= data_inicio) & (df_gastos["data"] <= data_fim)]

        if df_filtrado.empty:
            st.info("Nenhum gasto encontrado no período selecionado.")
        else:
            agrupado = df_filtrado.groupby("motivo")["valor"].sum().sort_values(ascending=False).reset_index()
            st.bar_chart(agrupado.rename(columns={"motivo": "Fornecedor", "valor": "Total Gasto"}).set_index("Fornecedor"))

            st.dataframe(agrupado, use_container_width=True, hide_index=True)

with aba6:
    st.subheader("🔍 Buscar Gastos")

    df = carregar_dados()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["data"])
    df["data"] = df["data"].dt.date  # Solo fecha

    termo = st.text_input("Buscar por carro, descrição, cliente, fornecedor ou placa").strip().lower()

    if termo:
        filtro = (
            df["carro"].astype(str).str.lower().str.contains(termo) |
            df["placa"].astype(str).str.lower().str.contains(termo) |
            df["descricao"].astype(str).str.lower().str.contains(termo) |
            df["cliente"].astype(str).str.lower().str.contains(termo) |
            df["motivo"].astype(str).str.lower().str.contains(termo)
        )
        resultados = df[filtro].sort_values("data", ascending=False)

        if resultados.empty:
            st.info("Nenhum resultado encontrado para o termo buscado.")
        else:
            st.markdown(f"### 🔎 {len(resultados)} resultado(s) encontrado(s)")
            st.dataframe(resultados, use_container_width=True, hide_index=True)
    else:
        st.info("Digite um termo para buscar nos registros.")
