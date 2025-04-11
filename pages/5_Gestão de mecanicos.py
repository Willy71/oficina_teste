import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --------------------------- CONFIG INICIAL ----------------------------------
st.set_page_config(page_title="Trabalhos por Mecânico", layout="wide", page_icon="🛠️")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main {
    background-color: #00001a;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Autenticación
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_INFO = st.secrets["gsheets"]
SPREADSHEET_KEY = '1kiXS0qeiCpWcNpKI-jmbzVgiRKrxlec9t8YQLDaqwU4'
SHEET_NAME = 'Hoja 1'

credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(credentials)
worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

@st.cache_data(ttl=600)
def cargar_datos():
    datos = worksheet.get_all_records()
    df = pd.DataFrame(datos)
    df["date_in"] = pd.to_datetime(df["date_in"], errors='coerce', dayfirst=True)
    df["date_out"] = pd.to_datetime(df.get("date_out", None), errors='coerce', dayfirst=True)
    
    # Convertir todos los valores de servicio a numéricos (del 1 al 12)
    for i in range(1, 13):
        df[f"valor_serv_{i}"] = pd.to_numeric(df.get(f"valor_serv_{i}", 0), errors='coerce')
    
    return df

def formatar_dos(valor):
    try:
        valor_float = float(valor)
        return f"{valor_float:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "0,00"

@st.cache_data(ttl=600)
def cargar_mecanicos():
    ws_mecanicos = gc.open_by_key(SPREADSHEET_KEY).worksheet("Mecanicos")
    nombres = ws_mecanicos.col_values(1)[1:]  # Ignorar header
    return [n.strip() for n in nombres if n.strip()]

# -------------------------- CONSULTA DE TRABAJOS ------------------------------
st.title("🛠️ Relatório de Trabalhos por Mecânico")

with st.sidebar:
    st.header("🔍 Filtros")
    data_inicial = st.date_input("Data inicial", datetime(datetime.now().year, datetime.now().month, 1))
    st.caption(f"📅 Início selecionado: {data_inicial.strftime('%d/%m/%Y')}")
    
    data_final = st.date_input("Data final", datetime.now())
    st.caption(f"📅 Fim selecionado: {data_final.strftime('%d/%m/%Y')}")

    comissao_pct = st.slider("% Comissão do mecânico", 0.0, 100.0, 40.0, step=5.0)

    mecanicos_lista = cargar_mecanicos()
    mecanico_filtro = st.selectbox("Filtrar por mecânico", options=["Todos"] + mecanicos_lista)

    atualizar = st.button("🔄 Atualizar relatório")

# ------------------------ FILTRAR E AGRUPAR ----------------------------------
if atualizar:
    df = cargar_datos()
    df_filtrado = df[(df['date_in'] >= pd.to_datetime(data_inicial)) & (df['date_in'] <= pd.to_datetime(data_final))]
    
    # Remover linhas sem mecânico
    df_filtrado = df_filtrado[df_filtrado['mecanico'].notna() & (df_filtrado['mecanico'] != '')]
    if mecanico_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["mecanico"] == mecanico_filtro]
    
    colunas_servicos = [f"valor_serv_{i}" for i in range(1, 13)]
    df_filtrado[colunas_servicos] = df_filtrado[colunas_servicos].fillna(0)
    df_filtrado["total_servicos"] = df_filtrado[colunas_servicos].sum(axis=1)

    
    # Agrupar por mecânico
    resultado = df_filtrado.groupby("mecanico")["total_servicos"].sum().reset_index()
    st.write(f"🔍 Total de ordens encontradas: {len(df_filtrado)}")
    resultado["comissao"] = resultado["total_servicos"] * (comissao_pct / 100)
    
    # -------------------------- EXIBIR RESULTADO ---------------------------------
    st.subheader("📊 Resumo por Mecânico")
    
    resultado["total_servicos_fmt"] = resultado["total_servicos"].apply(formatar_dos)
    resultado["comissao_fmt"] = resultado["comissao"].apply(formatar_dos)
    
    st.dataframe(resultado[["mecanico", "total_servicos_fmt", "comissao_fmt"]], use_container_width=True)
    
    
    # Mostrar totais
    total_carros = len(df_filtrado)
    total_geral = resultado["total_servicos"].sum()
    total_comissao = resultado["comissao"].sum()

    st.markdown(f"**🚗 Total de carros atendidos no período:** {total_carros}")
    st.markdown(f"**🔧 Total de serviços no período:** R$ {formatar_dos(total_geral)}")
    st.markdown(f"**💰 Total de comissões:** R$ {formatar_dos(total_comissao)} ({comissao_pct:.0f}%)")
    
    
    st.subheader("📄 Detalhes dos Serviços Realizados")

    df_filtrado["comissao"] = df_filtrado["total_servicos"] * (comissao_pct / 100)
    df_filtrado["total_servicos_fmt"] = df_filtrado["total_servicos"].apply(formatar_dos)
    df_filtrado["comissao_fmt"] = df_filtrado["comissao"].apply(formatar_dos)
    df_filtrado["date_in_fmt"] = df_filtrado["date_in"].dt.strftime("%d/%m/%Y")
    
    st.dataframe(df_filtrado[[
        "mecanico", "carro", "modelo", "placa", "date_in_fmt", "total_servicos_fmt", "comissao_fmt"
    ]], use_container_width=True)

 # ---------------------- GESTÃO DE MECÂNICOS ------------------------------
st.markdown("---")
st.subheader("🔧 Gerenciar lista de Mecânicos")

ws_mecanicos = gc.open_by_key(SPREADSHEET_KEY).worksheet("Mecanicos")
mecanicos_existentes = ws_mecanicos.col_values(1)[1:]  # Ignorar header

with st.expander("➕ Adicionar novo mecânico"):
    novo_mecanico = st.text_input("Nome do novo mecânico")
    if st.button("Adicionar", key="add_mecanico"):
        if novo_mecanico.strip() == "":
            st.warning("O nome não pode estar vazio.")
        elif novo_mecanico in mecanicos_existentes:
            st.warning("Esse mecânico já está na lista.")
        else:
            ws_mecanicos.append_row([novo_mecanico])
            st.success(f"Mecânico '{novo_mecanico}' adicionado com sucesso!")

with st.expander("📝 Editar ou remover mecânico existente"):
    mecanico_selecionado = st.selectbox("Selecione o mecânico", options=mecanicos_existentes)

    novo_nome = st.text_input("Editar nome", value=mecanico_selecionado, key="editar_nome")
    if st.button("Salvar edição"):
        cell = ws_mecanicos.find(mecanico_selecionado)
        ws_mecanicos.update_cell(cell.row, cell.col, novo_nome)
        st.success(f"Nome atualizado para '{novo_nome}'.")

    if st.button("Remover mecânico"):
        cell = ws_mecanicos.find(mecanico_selecionado)
        ws_mecanicos.delete_rows(cell.row)
        st.success(f"Mecânico '{mecanico_selecionado}' removido.")


    

    
