import streamlit as st
import pandas as pd
import gspread
import uuid
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from calendar import monthrange
import calendar

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

def carregar_dados():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    if "data_pag" in df.columns:
        df["data_pag"] = pd.to_datetime(df["data_pag"], dayfirst=True, errors='coerce').dt.date
        df["data_pag"] = df["data_pag"].fillna(df["data"])  # Rellena vacíos con 'data'
    
    print("Tipos de datos antes de conversión:", df.dtypes)
    
    if "valor" in df.columns:
        df["valor"] = df["valor"].astype(str)
        df["valor"] = df["valor"].apply(safe_float)
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors='coerce').dt.date
    
    print("Valores convertidos:", df["valor"].head())
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

    data_fmt = pd.to_datetime(data).strftime("%d/%m/%Y")
    data_pag_fmt = pd.to_datetime(data_pag if data_pag else data).strftime("%d/%m/%Y")

    nova_linha = [novo_id, data_fmt, data_pag_fmt, cliente, descricao, carro, placa, motivo, forma, valor, status]
    sheet.append_row(nova_linha)
    return novo_id

def atualizar_linha_por_id(id_alvo, novos_dados):
    df = carregar_dados()
    if id_alvo in df["ids"].values:
        linha = df[df["ids"] == id_alvo].index[0] + 2
        for i, valor in enumerate(novos_dados):
            sheet.update_cell(linha, i + 1, valor)
        return True
    return False

def excluir_linha_por_id(id_alvo):
    df = carregar_dados()
    if id_alvo in df["ids"].values:
        linha = int(df[df["ids"] == id_alvo].index[0]) + 2
        sheet.delete_rows(linha)
        return True
    return False

def formatar_valor(valor, padrao=""):
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
    try:
        if pd.isna(valor) or valor in [None, '']:
            return f"R$ {padrao}"
        
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".")
        
        valor_float = float(valor)
        return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"R$ {padrao}"

def normalize_status(status):
    if pd.isna(status):
        return "pendente"
    
    status = str(status).strip().lower()
    
    if status in ['entrada', 'entradas', 'ingreso', 'ingresos', 'income', 'in']:
        return 'entrada'
    elif status in ['saida', 'saída', 'salida', 'gasto', 'gastos', 'out', 'expense']:
        return 'saida'
    elif status in ['pendente', 'pendientes', 'pending', 'pend']:
        return 'pendente'
    
    return status

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
                st.rerun()

with aba2:
    st.subheader("📋 Lançamentos")
    df = carregar_dados()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["data"])
    df["data"] = df["data"].dt.date

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
    df["ids"] = df["ids"].astype(int)

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
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["valor"] = df["valor"].apply(safe_float)
    df["data_pag"] = pd.to_datetime(df["data_pag"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["data_pag"])
    df["data_pag"] = df["data_pag"].dt.date

    if df.empty:
        st.warning("Não há dados com datas válidas.")
    else:
        data_min = min(df["data_pag"])
        data_max = max(df["data_pag"])
        st.caption(f"📅 Datas disponíveis: de {data_min.strftime('%d/%m/%Y')} até {data_max.strftime('%d/%m/%Y')}")
        
        col_mes, col_ano = st.columns(2)
        meses = {
            0: "Todos os períodos...",
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        mes_selecionado = col_mes.selectbox("Mês", options=list(meses.keys()), format_func=lambda x: meses[x], index=0)
        ano_atual = date.today().year
        ano_selecionado = col_ano.selectbox("Ano", options=list(range(ano_atual, ano_atual - 6, -1)))
        
        if mes_selecionado != 0:
            primeiro_dia = date(ano_selecionado, mes_selecionado, 1)
            ultimo_dia = date(ano_selecionado, mes_selecionado, monthrange(ano_selecionado, mes_selecionado)[1])
        else:
            primeiro_dia = data_min
            ultimo_dia = data_max

        data_inicio_padrao = max(min(primeiro_dia, data_max), data_min)
        data_fim_padrao = max(min(ultimo_dia, data_max), data_inicio_padrao)
        
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input(
                "Data início", 
                value=data_inicio_padrao,
                min_value=data_min,
                max_value=data_max,
                key="inicio_resumo"
            )
        with col2:
            data_fim = st.date_input(
                "Data fim", 
                value=data_fim_padrao,
                min_value=data_inicio,
                max_value=data_max,
                key="fim_resumo"
            )

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
        st.markdown("### 📋 Filtrar lançamentos por tipo")
        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([3.5,0.5,3.5,0.5,3.5,0.5,3.5,1,1,1])
        mostrar_tipo = None
        with col1:
            if st.button("🟢 Entradas", key="btn_resumo_entradas", use_container_width=True):
                mostrar_tipo = "entrada"
        with col3:
            if st.button("🔴 Saídas", key="btn_resumo_saidas", use_container_width=True):
                mostrar_tipo = "saida"
        with col5:
            if st.button("🟡 Pendentes", key="btn_resumo_pendentes", use_container_width=True):
                mostrar_tipo = "pendente"
        with col7:
            if st.button("📋 Todos", key="btn_resumo_todos", use_container_width=True):
                mostrar_tipo = "todos"

        if mostrar_tipo:
            if mostrar_tipo == "todos":
                df_tipo = df_filtrado
                st.markdown("#### 📋 Todos os lançamentos")
            else:
                df_tipo = df_filtrado[df_filtrado["status"] == mostrar_tipo]
                cor = {"entrada": "🟢", "saida": "🔴", "pendente": "🟡"}[mostrar_tipo]
                titulo = {"entrada": "Entradas", "saida": "Saídas", "pendente": "Pendentes"}[mostrar_tipo]
                st.markdown(f"#### {cor} {titulo}")
                
            st.dataframe(df_tipo.sort_values("data_pag", ascending=False), use_container_width=True, hide_index=True)

        # --- NOVA TABELA DE RESUMO ANUAL ---
        st.markdown("---")
        if ano_selecionado:
            st.markdown(f"### Resumo Anual para {ano_selecionado}")
            df_ano = df[df['data_pag'].map(lambda x: x.year) == ano_selecionado]
            
            dados_anuais = []
            for mes_num in range(1, 13):
                df_mes = df_ano[df_ano['data_pag'].map(lambda x: x.month) == mes_num]
                
                entradas = df_mes[df_mes['status'] == 'entrada']['valor'].sum()
                saidas = df_mes[df_mes['status'] == 'saida']['valor'].sum()
                pendentes = df_mes[df_mes['status'] == 'pendente']['valor'].sum()
                lucro = entradas - saidas
                
                dados_anuais.append({
                    "Mês": meses[mes_num],
                    "Ano": ano_selecionado,
                    "Entradas": entradas,
                    "Saídas": saidas,
                    "Pendentes": pendentes,
                    "Lucro Mensal": lucro
                })
            
            tabela_anual = pd.DataFrame(dados_anuais)
            tabela_anual['Entradas'] = tabela_anual['Entradas'].apply(formatar_real)
            tabela_anual['Saídas'] = tabela_anual['Saídas'].apply(formatar_real)
            tabela_anual['Pendentes'] = tabela_anual['Pendentes'].apply(formatar_real)
            tabela_anual['Lucro Mensal'] = tabela_anual['Lucro Mensal'].apply(formatar_real)
            st.dataframe(tabela_anual, use_container_width=True, hide_index=True)
        # --- FIM DA NOVA TABELA ---

with aba5:
    st.subheader("📈 Análise de Gastos por Fornecedor")
    df = carregar_dados()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["valor"] = df["valor"].apply(safe_float)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["data"])
    df["data"] = df["data"].dt.date

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
    df["data"] = df["data"].dt.date

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
