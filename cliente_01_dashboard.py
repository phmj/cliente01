import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
#import os
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Analise financeira - Cliente 01!!!", page_icon=":bar_chart:")

st.title(" :bar_chart: Análise Financeira - Cliente 01")
# Forca o titulo a ficar no topo
st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)

# Insere o arquivo excel para analise
f1 = st.file_uploader(":file_folder: Upload a file", type=(["xlsx"]))
df = pd.read_excel('resumo_st.xlsx')
# Nao prossegue sem carregar o arquivo
if f1 == None:
    st.info('Carregue o arquivo')
    st.stop()

#st.write(df.head())
# Carrega diretamente o arquivo para acelerar
#df = pd.read_csv("Superstore.csv", encoding = "ISO-8859-1",delimiter=";")

#===============================================
# Cleannig data
#===============================================
# Retirar aplicacoes e resgates da analise
mask = (df['classificacao'] == 'aplicacao')
df = df[~mask]
df["data"] = pd.to_datetime(df["data"],format='%d/%m/%y')
df["mes_ano"] = df["data"].dt.to_period("M").dt.strftime("%m/%Y")
# forca valores positivos para saida
df['R$_abs'] = df['R$'].abs()
# Preenche os campos sem classificacao como 'outros'
df['classificacao'] = df['classificacao'].fillna('sem classif.')
# Os valores positivos sao classificados como receitas
mask = df['R$'] > 0
df.loc[mask, 'classificacao'] = 'Receita'
# Retirar aplicacoes e resgates da analise
#mask = (df['classificacao'] == 'aplicacao')
#df = df[~mask]

#df['Sales'] = df['Sales'].apply(lambda x: x.replace(',','.'))
#df['Sales'] = df['Sales'].astype('float64')

#col1, col2 = st.columns((2), gap='medium')
#df["Order Date"] = pd.to_datetime(df["Order Date"],format='%d/%m/%Y')

## Getting the min and max date 
#startDate1 = df["data"].min()
#endDate1 = df["data"].max()
## Mostra as datas iniciais e finais extraidas do arquivo e 
## permite periodos inferiores
#col1, col2 = st.columns((2), gap='medium')
#with col1:
#    date1 = pd.to_datetime(st.date_input("Start Date", startDate1))
#
#with col2:
#    date2 = pd.to_datetime(st.date_input("End Date", endDate1))
#    
#st.write('==> antes de filtrar a data =',df.shape)
#df = df[(df["data"] >= date1) & (df["data"] <= date2)].copy()
#st.write('==> depois de filtrar a data =',df.shape)
#st.write('==> Período selecionado de %s a %s' % (date1.strftime('%d/%m/%Y'),date2.strftime('%d/%m/%Y')))

#===============================================
# Barra Lateral para filtrar os dados
#===============================================
st.sidebar.header("==> Selecione seus filtros: ")

# Selecao do periodo de analise
start_month, end_month = st.sidebar.select_slider(
    'Período de análise:',
    options=['Set23', 'Out23', 'Nov23','Dez23','Jan24'],
    value=('Set23', 'Nov23')
)
data_ini_vet = dict({'Set23':'01/09/23','Out23':'01/10/23','Nov23':'01/11/23'})
data_fim_vet = dict({'Set23':'30/09/23','Out23':'31/10/23','Nov23':'30/11/23'})
startDate = pd.to_datetime(data_ini_vet[start_month],format='%d/%m/%y')
endDate = pd.to_datetime(data_fim_vet[end_month],format='%d/%m/%y')
#st.write(startDate,endDate)
#st.write('==> Período de análise meses', start_month, 'até', end_month)

#date1 = startDate
#date2 = endDate
df1 = df[(df["data"] >= startDate) & (df["data"] <= endDate)].copy()
#st.write(df1.shape)
#st.write(df1)

# Selecao por Fluxo(entrada/saida)
fluxo = st.sidebar.multiselect("Coluna Fluxo - escolha entradas ou saidas", df["fluxo"].unique())
if not fluxo:
    df2 = df1.copy()
else:
    df2 = df1[df1["fluxo"].isin(fluxo)]

# Selecao por Classificacao
classif = st.sidebar.multiselect("Coluna Classificacao - detalhes por item", np.sort(df2["classificacao"].unique()))
if not classif:
    df3 = df2.copy()
else:
    df3 = df2[df2["classificacao"].isin(classif)]

# Dados filtrados com base em fluxo, categoria, ...
filtered_date = df1
filtered_df = df3

#===============================================
# STREAMLIT LAYOUT]
#===============================================

# Graficos
category_df = filtered_date.groupby(by = ["fluxo"], as_index = False)["R$_abs"].sum()
#fluxo_period = category_df[category_df['fluxo']=='entrada']['R$'].values[0] - \
#                category_df[category_df['fluxo']=='saida']['R$'].values[0]
#fluxo_per = 
#st.write('==> A variação no periodo foi de: R$ %.2f' % (fluxo_period))
#st.write('===========================================')
#
col1, col2 = st.columns((2), gap='medium')
with col1:
    st.subheader("Fluxo no período")
    fig = px.bar(category_df, x = "fluxo", y = "R$_abs", text = ['${:,.2f}'.format(x) \
        for x in category_df["R$_abs"]],template = "seaborn")
    st.plotly_chart(fig,use_container_width=True, height = 20)

#with col2:
#    st.subheader("")
#    fig = px.pie(filtered_df, values = "R$", names = "fluxo", hole = 0.5)
#    #fig.update_traces(text = filtered_df["Region"], textposition = "outside")
#    st.plotly_chart(fig,use_container_width=True)

linechart = pd.DataFrame(filtered_date.groupby(df["mes_ano"])["R$"].sum()).reset_index()

#col3,col4 = st.columns(2)
with col2:
    st.subheader("Saldo por mês")
    fig = px.line(linechart, x = "mes_ano", y="R$", labels = {"Sales": "Amount"},\
               height=300, width = 500,template="gridon")
    #fig = px.bar(category_df, x = "fluxo", y = "R$", text = ['${:,.2f}'.format(x) \
    #    for x in category_df["R$"]],template = "seaborn")
    st.plotly_chart(fig,use_container_width=True)
    

classif_df = filtered_df.groupby(by = ["classificacao"], as_index = False)["R$"].\
              sum().sort_values('R$',ascending=False)
#st.write(classif_df)

#col1, col2 = st.columns((3,6))
cool1, cool2 = st.columns(2)
with cool1:
    st.subheader("Classificação no período")
    fig = px.bar(classif_df, x = "classificacao", y = "R$", text = ['${:,.2f}'.format(x) for x in classif_df["R$"]],
                 template = "seaborn")
    fig.update_layout(height=400,margin=dict(l=50, r=10, t=100, b=10, pad=8))
    st.plotly_chart(fig,use_container_width=True)

dados = pd.DataFrame(filtered_df[["mes_ano",'classificacao','R$']].\
                     groupby(by=["mes_ano",'classificacao']).sum()).reset_index()

#template="gridon"
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


#with cool2:
#    st.subheader("Classificação - %")
#    fig = px.pie(filtered_df, values = "R$_abs", names = "classificacao", hole = 0.5)
#    fig.update_layout(height=400,margin=dict(l=50, r=10, t=100, b=10, pad=8))
#    #fig.update_traces(text = filtered_df["Region"], textposition = "outside")
#    st.plotly_chart(fig,use_container_width=True)

# Mostra detalhes dos dados dos graficos
cl1,cl2 = st.columns((2))
with cl1:
    with st.expander("Classificacao_ViewData"):
        st.write(classif_df.style.background_gradient(cmap="Blues"))

with cl2:
    st.write('')
    
#st.write('===========================================')

#st.write('==> df =',df.shape)
#st.write('==> df2(fluxo) =',df2.shape)
#st.write('==> df3(classificacao) =',df3.shape)

#st.slider('data',value=(startDate,endDate))


# This container will be displayed below the first one
#with st.container():
#    col1, col2 = st.columns(2, gap="large")
#    with col1:
#        st.header("Continental emissions since 1850")  
#        st.info("Select a single continent or compare continents")
#        
#        # code to draw the single continent data

#    with col2:
#        st.header("Continental emissions since 1850")
#        st.info("To add a continent select it from the menu. You can also delete one, too")

#        # code to draw the compared continent data

#from datetime import datetime

#start_time,end_time = st.slider(
#    "When do you start?",
#    value=(datetime(2020, 1, 1),datetime(2021, 1, 1)))
#st.write("Start time:", start_time)
#st.write("End time:", end_time)

#st.write(type(startDate))
#st.write(type(start_time))