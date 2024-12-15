import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
import os


st.set_page_config(layout="wide", page_title="Dashboard de Validade de Produtos")

# Função para verificar status de validade
def verificar_status(data_validade):
    hoje = dt.date.today()
    delta = (data_validade - hoje).days

    if delta < 0:
        return "Vencido"
    elif delta <= 3:
        return "Próximo ao Vencimento"
    else:
        return "Dentro do Prazo"


# Inicializando ou carregando o arquivo de etiquetas
etiquetas_arquivo = "etiquetas.csv"

if not os.path.exists(etiquetas_arquivo):
    df = pd.DataFrame(columns=["Codigo_Barras", "Data_Validade", "Status"])
    df.to_csv(etiquetas_arquivo, index=False)
else:
    df = pd.read_csv(etiquetas_arquivo)
    df["Data_Validade"] = pd.to_datetime(df["Data_Validade"], format="%Y-%m-%d").dt.date
    df["Status"] = df["Data_Validade"].apply(verificar_status)

# Inicializando ou carregando o arquivo de metas diárias
metas_arquivo = "metas.csv"

if not os.path.exists(metas_arquivo):
    metas_df = pd.DataFrame(columns=["Data", "Pontuacao"])
    metas_df.to_csv(metas_arquivo, index=False)
else:
    metas_df = pd.read_csv(metas_arquivo)


# Função para adicionar dias sem acesso
def atualizar_metas_diarias():
    hoje = dt.date.today()
    if not metas_df.empty:
        ultima_data = pd.to_datetime(metas_df["Data"].max()).date()
        dias_sem_acesso = (hoje - ultima_data).days

        if dias_sem_acesso > 1:
            # Criando uma lista de datas em que não houve acesso
            dias_faltantes = [
                (ultima_data + dt.timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(1, dias_sem_acesso)
            ]
            # Criando um DataFrame com esses dias e atribuindo pontuação 0
            registros_faltantes = pd.DataFrame({
                "Data": dias_faltantes,
                "Pontuacao": [0] * len(dias_faltantes)
            })

            # Atualizando o histórico
            metas_df_updated = pd.concat([metas_df, registros_faltantes], ignore_index=True)
            metas_df_updated.to_csv(metas_arquivo, index=False)
            return metas_df_updated
    return metas_df


# Atualizando metas para incluir lacunas sem acesso
metas_df = atualizar_metas_diarias()

# Verificar se o usuário já pontuou hoje
hoje = dt.date.today()

if hoje.strftime("%Y-%m-%d") not in metas_df["Data"].values:
    nova_pontuacao = 10  # Pontuação diária padrão
    novo_registro = pd.DataFrame({"Data": [hoje.strftime("%Y-%m-%d")], "Pontuacao": [nova_pontuacao]})
    metas_df = pd.concat([metas_df, novo_registro], ignore_index=True)
    metas_df.to_csv(metas_arquivo, index=False)
    st.sidebar.success(f"Você ganhou {nova_pontuacao} pontos por acessar hoje!")

# Exibir pontuação acumulada
pontuacao_total = metas_df["Pontuacao"].sum()
st.sidebar.header("Pontuação de Metas Diárias")
st.sidebar.write(f"Pontuação total acumulada: **{pontuacao_total} pontos**")

# Exibição de gráfico da pontuação diária
grafico_metas = px.bar(
    metas_df,
    x="Data",
    y="Pontuacao",
    title="Histórico de Pontuação Diária",
    labels={"Data": "Data de Acesso", "Pontuacao": "Pontuação"},
    text="Pontuacao"
)
st.sidebar.plotly_chart(grafico_metas, use_container_width=True)

# Título principal
st.title("Dashboard de Controle de Validade de Produtos")

# Sidebar - Adicionar novo produto
st.sidebar.header("Adicionar Novo Produto")
codigo_barras = st.sidebar.text_input("Código de Barras")
data_validade_input = st.sidebar.date_input("Data de Validade")

if st.sidebar.button("Adicionar Produto"):
    if codigo_barras and data_validade_input:
        novo_produto = pd.DataFrame({
            "Codigo_Barras": [codigo_barras],
            "Data_Validade": [data_validade_input],
            "Status": [verificar_status(data_validade_input)]
        })
        df = pd.concat([df, novo_produto], ignore_index=True)
        df.to_csv(etiquetas_arquivo, index=False)
        st.sidebar.success("Produto adicionado com sucesso!")
    else:
        st.sidebar.error("Preencha todos os campos para adicionar um produto.")

# Sidebar - Filtros
st.sidebar.header("Filtros")
status_filter = st.sidebar.multiselect(
    "Filtrar por Status", options=df["Status"].unique(), default=df["Status"].unique()
)

# Sidebar - Gerenciar dados
st.sidebar.header("Gerenciar Dados")

# Apagar um produto por posição
posicao_para_apagar = st.sidebar.number_input(
    "Posição do Produto para Apagar (índice na tabela)", min_value=0, step=1, value=0
)
if st.sidebar.button("Apagar Produto"):
    if not df.empty and posicao_para_apagar < len(df):
        df = df.drop(df.index[posicao_para_apagar]).reset_index(drop=True)
        df.to_csv(etiquetas_arquivo, index=False)
        st.sidebar.success(f"Produto na posição {posicao_para_apagar} apagado com sucesso!")
    else:
        st.sidebar.error("Índice inválido ou tabela vazia.")

# Exportar dados para CSV
st.sidebar.subheader("Exportar Dados")
if st.sidebar.button("Exportar para CSV"):
    if not df.empty:
        df.to_csv("produtos_validade.csv", index=False)
        st.sidebar.success("Arquivo 'produtos_validade.csv' gerado com sucesso!")
    else:
        st.sidebar.error("Nenhum dado disponível para exportação.")

# Filtrar dados para exibição
if not df.empty:
    df_filtered = df[df["Status"].isin(status_filter)]
else:
    df_filtered = pd.DataFrame(columns=df.columns)

# Cores para os status
cores = {
    "Vencido": "#fe4a23",
    "Próximo ao Vencimento": "#ffcf28",
    "Dentro do Prazo": "#09b96d"
}

# Layout principal
c1, c2 = st.columns([0.6, 0.4])

# Exibir tabela de produtos filtrados
c1.subheader("Tabela de Produtos Filtrados")
if not df_filtered.empty:
    c1.dataframe(df_filtered)
else:
    c1.write("Nenhum dado para exibir.")

# Exibir gráfico de distribuição por status
if not df_filtered.empty:
    status_distribution = df_filtered["Status"].value_counts().reset_index()
    status_distribution.columns = ["Status", "Quantidade"]

    status_distribution["Cor"] = status_distribution["Status"].map(cores)

    fig = px.pie(
        status_distribution,
        values="Quantidade",
        names="Status",
        color="Status",
        color_discrete_map=cores,
        title="Distribuição de Produtos por Status",
        hole=0.3
    )

    c2.plotly_chart(fig, use_container_width=True)
