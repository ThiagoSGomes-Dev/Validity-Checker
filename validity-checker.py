import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard de Validade de Produtos")

def verificar_status(data_validade):
    hoje = dt.date.today()
    delta = (data_validade - hoje).days

    if delta < 0:
        return "Vencido"
    elif delta <= 3:
        return "Próximo ao Vencimento"
    else:
        return "Dentro do Prazo"


try:
    df = pd.read_csv("etiquetas.csv")
    df["Data_Validade"] = pd.to_datetime(df["Data_Validade"], format="%Y-%m-%d").dt.date
    df["Status"] = df["Data_Validade"].apply(verificar_status)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Codigo_Barras", "Data_Validade", "Status"])

st.title("Dashboard de Controle de Validade de Produtos")

st.sidebar.header("Adicionar Novo Produto")
codigo_barras = st.sidebar.text_input("Código de Barras")
data_validade_input = st.sidebar.date_input("Data de Validade", min_value=dt.date.today())

if st.sidebar.button("Adicionar Produto"):
    if codigo_barras and data_validade_input:
        novo_produto = pd.DataFrame({
            "Codigo_Barras": [codigo_barras],
            "Data_Validade": [data_validade_input],
            "Status": [verificar_status(data_validade_input)]
        })
        df = pd.concat([df, novo_produto], ignore_index=True)
        df.to_csv("etiquetas.csv", index=False)
        st.sidebar.success("Produto adicionado com sucesso!")
    else:
        st.sidebar.error("Preencha todos os campos para adicionar um produto.")

st.sidebar.header("Filtros")
status_filter = st.sidebar.multiselect(
    "Filtrar por Status", options=df["Status"].unique(), default=df["Status"].unique()
)

if not df.empty:
    df_filtered = df[df["Status"].isin(status_filter)]
else:
    df_filtered = pd.DataFrame(columns=df.columns)

cores = {
    "Vencido": "#fe4a23",
    "Próximo ao Vencimento": "#ffcf28",
    "Dentro do Prazo": "#09b96d"
}

c1, c2 = st.columns([0.6, 0.4])

c1.subheader("Tabela de Produtos Filtrados")
if not df_filtered.empty:
    c1.dataframe(df_filtered)
else:
    c1.write("Nenhum dado para exibir.")

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

st.sidebar.subheader("Exportar Dados")
if st.sidebar.button("Exportar para CSV"):
    if not df_filtered.empty:
        df_filtered.to_csv("produtos_validade.csv", index=False)
        st.sidebar.success("Arquivo 'produtos_validade.csv' gerado com sucesso!")
    else:
        st.sidebar.error("Nenhum dado disponível para exportação.")
