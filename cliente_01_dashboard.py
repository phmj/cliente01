import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
#import os
import warnings
warnings.filterwarnings('ignore')

# Descritivo na barra do browser
st.set_page_config(page_title="Analise financeira - Cliente 01!!!", page_icon=":bar_chart:")
# Título da pagina
st.title(" :bar_chart: Análise Financeira - Cliente 01")
# Forca o titulo a ficar no topo
st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)

#===============================================
# Insere o arquivo excel para analise
#===============================================
f1 = st.file_uploader(":file_folder: Upload a file", type=(["xlsx"]))
# Nao prossegue sem carregar o arquivo
if f1 == None:
    st.info('Carregue o arquivo')
    st.stop()
# carrega o arquivo selecionado    
df = pd.read_excel(f1)
#df = pd.read_excel('resumo_st_new.xlsx')

#===============================================
# Preparação dos dados
#===============================================
# ==> Cleannig data
# 1) Retirar aplicacoes e resgates da analise
mask = (df['classificacao'] == 'aplicacao')
df = df[~mask]
# 2) Converte data to datetime
df["data"] = pd.to_datetime(df["data"],format='%d/%m/%y')
# ==> Feature engeneering
# 1) Nova coluna com somente mes-ANO
df["mes_ano"] = df["data"].dt.to_period("M").dt.strftime("%m/%Y")
# 2) Nova coluna com somente valores positivos tanto entrada como saida
df['R$_abs'] = df['R$'].abs()
# ==> Tratamento de dados com falta de informacao
# 1) Preenche os campos sem classificacao como 'sem classif.'
df['classificacao'] = df['classificacao'].fillna('sem classif.')
# 2) Os valores positivos sao classificados genericamente como Receita
mask = df['R$'] > 0
df.loc[mask, 'classificacao'] = 'Receita'


#===============================================
# Barra Lateral para filtrar os dados
#===============================================
st.sidebar.header("==> Selecione seus filtros: ")

# ==> Selecao do periodo de analise
# Acrescentar dados com o aumento do periodo de tempo fornecido
start_month, end_month = st.sidebar.select_slider(
    'Período de análise:',
    options=['Set23', 'Out23', 'Nov23','Dez23','Jan24'],
    value=('Set23', 'Dez23')
)
data_ini_vet = dict({'Set23':'01/09/23','Out23':'01/10/23','Nov23':'01/11/23','Dez23':'01/12/23'})
data_fim_vet = dict({'Set23':'30/09/23','Out23':'31/10/23','Nov23':'30/11/23','Dez23':'31/12/23'})
startDate = pd.to_datetime(data_ini_vet[start_month],format='%d/%m/%y')
endDate = pd.to_datetime(data_fim_vet[end_month],format='%d/%m/%y')
# Filtra o periodo de acordo com a selecao
df1 = df[(df["data"] >= startDate) & (df["data"] <= endDate)].copy()

# ==> Selecao por Fluxo(entrada/saida)
fluxo = st.sidebar.multiselect("Coluna Fluxo - escolha entradas ou saidas", df["fluxo"].unique())
if not fluxo:
    df2 = df1.copy()
else:
    df2 = df1[df1["fluxo"].isin(fluxo)]

# ==> Selecao por Classificacao
classif = st.sidebar.multiselect("Coluna Classificacao - detalhes por item", np.sort(df2["classificacao"].unique()))
if not classif:
    df3 = df2.copy()
else:
    df3 = df2[df2["classificacao"].isin(classif)]

# Dados filtrados com base em fluxo, categoria, ...
filtered_date = df1
filtered_df = df3

#===============================================
# Graficos
#===============================================
# 1) Grafico de barras entradas e saidas do período
category_df = filtered_date.groupby(by = ["fluxo"], as_index = False)["R$_abs"].sum()
# 2) Grafico de linhas do saldo(entradas e saídas) por mes
linechart = pd.DataFrame(filtered_date.groupby(df["mes_ano"])["R$"].sum()).reset_index()
# 3) Grafico de linhas das entradas por mes
filtered_date_ent = df.query('fluxo == "entrada"')
linechart_ent = pd.DataFrame(filtered_date_ent.groupby(df["mes_ano"])["R$_abs"].sum()).reset_index()
linechart_ent['fluxo'] = 'entrada'
# 4) Grafico de linhas das saídas por mes
filtered_date_sai = df.query('fluxo == "saida"')
linechart_sai = pd.DataFrame(filtered_date_sai.groupby(df["mes_ano"])["R$_abs"].sum()).reset_index()
linechart_sai['fluxo'] = 'saida'
linechart_ent_sai = pd.concat([linechart_ent,linechart_sai])
# 5) Grafico de barras - classificação no período
classif_df = filtered_df.groupby(by = ["classificacao"], as_index = False)["R$"].\
              sum().sort_values('R$',ascending=False)
# 6) Grafico de linhas - classificação por mes
dados = pd.DataFrame(filtered_df[["mes_ano",'classificacao','R$']].\
                     groupby(by=["mes_ano",'classificacao']).sum()).reset_index()



#===============================================
# STREAMLIT LAYOUT DE PAGINA
#===============================================
#col1,col2 = st.columns((2), gap='medium')
#col3,col4 = st.columns((2))

# ==> Visão geral - afetada somente pelo primeiro filtro da aba lateral
st.write(' ====================================================')
st.write("==> Visão geral no Período Selecionado")
st.write(' ====================================================')
with st.container(border=True):
    col1,col2 = st.columns((2), gap='medium')
    col3,col4 = st.columns((2))
    # Grafico 1
    with col1:
        st.subheader("Fluxo acumulado no período")
        fig = px.bar(category_df, x = "fluxo", y = "R$_abs", text = ['${:,.2f}'.format(x) \
            for x in category_df["R$_abs"]],template = "seaborn")
        st.plotly_chart(fig,use_container_width=True, height = 20)
        st.info("Apresenta a soma de entradas(positivo) e saídas(negativo) \
                no período selecionado")

    # Grafico 2
    with col2:
        st.subheader("Saldo por mês")
        fig = px.line(linechart, x = "mes_ano", y="R$", labels = {"mes_ano": "Mês_ano"},\
                height=300, width = 500,template="gridon")
        #fig = px.bar(category_df, x = "fluxo", y = "R$", text = ['${:,.2f}'.format(x) \
        #    for x in category_df["R$"]],template = "seaborn")
        st.plotly_chart(fig,use_container_width=True)
        st.info("Apresenta a diferença entre entradas e saídas ao longo de cada mês. \
                O objetivo é sempre estar com este valor positivo.")

    with col3:
        st.subheader('Evolução saldo empréstimos por mês')
        st.info("Apresenta o comportamento dos empréstimos por mês. Os empréstimos tem juros \
            associados e portanto impactam na despesa financeira.")

    # Grafico 3
    with col4:
        st.subheader("Entradas/Saídas por mês")
        fig = px.line(linechart_ent_sai, x="mes_ano",y="R$_abs",color="fluxo",
                    color_discrete_map = {
                        'entrada': 'green',
                        'saida':'red'
                    },
                labels= {"mes_ano": "Mês_ano",
                        "R$_abs": "R$"},
                width=500,
                height=400)
        fig.update_layout(height=400,margin=dict(l=50, r=10, t=100, b=10, pad=8),\
                legend=dict(orientation='h',title='Legenda',
                        y=1,x=1,xanchor='right',yanchor='bottom'))
        st.plotly_chart(fig,use_container_width=True)
        st.info("Apresenta o detalhamento das entradas e saídas ao longo de cada mês. \
                    O objetivo é sempre estar com o gráfico de entrada superior a \
                        saída. A diferença entre estes gráficos é que produz o gráfico do fluxo.")

st.write(' ====================================================')
#st.info("Detalhamento")
st.write("==> Detalhamento")
st.write(' ====================================================')

with st.container(border=True):
    cool1, cool2 = st.columns(2)
    # Grafico 4
    with cool1:
        st.subheader("Classificação no período")
        fig = px.bar(classif_df, x = "classificacao", y = "R$", text = ['${:,.2f}'.format(x) for x in classif_df["R$"]],
                    template = "seaborn")
        fig.update_layout(height=400,margin=dict(l=50, r=10, t=100, b=10, pad=8))
        st.plotly_chart(fig,use_container_width=True)
        st.info("Neste gráfico  de barras importante observar que as receitas são colocadas  \
                como positivas e as saídas como negativas. Importante analisar entradas e saídas \
                    separadamente usando a seleção na barra lateral na coluna fluxo.")

    # Grafico 5
    with cool2:
        st.subheader("Classificação por mês")
        fig = px.line(dados, x = "mes_ano", y='R$', color='classificacao',\
                height=400, width = 600,template="seaborn")
    #   fig = px.pie(dados, values = "R$_abs", names = "classificacao", hole = 0.5)
        fig.update_layout(height=400,margin=dict(l=50, r=10, t=100, b=10, pad=8),\
            legend=dict(orientation='h',title='Legenda',
                    y=1,x=1,xanchor='right',yanchor='bottom'))
        #fig.update_traces(text = filtered_df["Region"], textposition = "outside")
        st.plotly_chart(fig,use_container_width=True)
        st.info("Permite analisar o andamento dos items classificados por mês. \
            Usando a coluna classificação na barra lateral é possivel ver itens  \
                ou conjunto de itens com \
                mais detalhe. Importante focar naqueles de maior \
                    valor para obter maior efeito.")


    # Dados de classificacao em forma de tabela
    cl1,cl2 = st.columns((2))
    with cl1:
        st.info("Se quiser ver os dados em forma de tabela clique na seta abaixo")
        with st.expander("Classificacao_ViewData"):
            st.write(classif_df.style.background_gradient(cmap="Blues"))
            st.info("Dados em ordem descrescente de valor.")

    with cl2:
        st.write('')
    

