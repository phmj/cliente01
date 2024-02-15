import streamlit as st
import plotly.express as px
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
#import os
import warnings

warnings.filterwarnings('ignore')

# Descritivo na barra do browser
st.set_page_config(page_title="Analise financeira - Cliente 01!!!", page_icon=":bar_chart:",layout="wide" )
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
df_raw = pd.read_excel(f1)
#df_raw = pd.read_excel('resumo_ori_class_full_050224.xlsx')

#===============================================
# Preparação dos dados
#===============================================
# ==> Cleannig data
# 1) Converte data to datetime
df_raw["data"] = pd.to_datetime(df_raw["data"],format='%d/%m/%y')
# 2) Mascara p/ retirar aplicacoes e resgates da analise
mask1 = (df_raw['classificacao'] == 'aplicacao')
# 3) Mascara p/ retirar status das reservas(investimento ou divida)
mask2 = (df_raw['classificacao'] == 'divida')
# ==> Dados para analise de fluxo
mask_fluxo = mask1 | mask2
df = df_raw[~mask_fluxo].copy()
# ==> Dados para analise dos emprestimos
mask_emp = ~mask1 & mask2
df_emp = df_raw[mask_emp].copy()
# ==> Feature engeneering
# 4) Nova coluna com somente mes-ANO
#df["mes_ano"] = df["data"].dt.to_period("M").dt.strftime("%m/%Y")
df["mes_ano"] = df["data"].dt.to_period("M")
df_emp["mes_ano"] = df_emp["data"].dt.to_period("M")
# 2) Nova coluna com somente valores positivos tanto entrada como saida
df['R$_abs'] = df['R$'].abs()
# ==> Tratamento de dados com falta de informacao
# 1) Preenche os campos sem classificacao como 'sem classif.'
df['classificacao'] = df['classificacao'].fillna('sem classif.')


#===============================================
# Barra Lateral para filtrar os dados
#===============================================
st.sidebar.header("==> Selecione seus filtros: ")

# ==> Selecao do periodo de analise
# Acrescentar dados com o aumento do periodo de tempo fornecido
start_month, end_month = st.sidebar.select_slider(
    'Período de análise:',
    options=['Set23', 'Out23', 'Nov23','Dez23','Jan24'],
    value=('Set23', 'Jan24')
)
data_ini_vet = dict({'Set23':'01/09/23','Out23':'01/10/23','Nov23':'01/11/23','Dez23':'01/12/23','Jan24':'01/01/24'})
data_fim_vet = dict({'Set23':'30/09/23','Out23':'31/10/23','Nov23':'30/11/23','Dez23':'31/12/23','Jan24':'31/01/24'})
startDate = pd.to_datetime(data_ini_vet[start_month],format='%d/%m/%y')
endDate = pd.to_datetime(data_fim_vet[end_month],format='%d/%m/%y')
# Filtra o periodo de acordo com a selecao
df1 = df[(df["data"] >= startDate) & (df["data"] <= endDate)].copy()
df_emp1 = df_emp[(df_emp["data"] >= startDate) & (df_emp["data"] <= endDate)].copy()

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
filtered_emp_date = df_emp1
filtered_df = df3

#===============================================
# Graficos
#===============================================
# ==> Arquivo de entradas e saidas
# 1) Grafico de barras entradas e saidas do período
bar_fluxo_rec_pos_df = filtered_date.groupby(by = ["fluxo"], as_index = False)["R$_abs"].sum()

# 2) Grafico de linhas do saldo(entradas e saídas) por mes
line_mes_rec_df = pd.DataFrame(filtered_date.groupby(df["mes_ano"])["R$"].sum()).reset_index()

# 3) Grafico de linhas das entradas por mes
filtered_date_ent_df = filtered_date.query('fluxo == "entrada"')
line_mes_ent_df = pd.DataFrame(filtered_date_ent_df.groupby(df["mes_ano"])["R$_abs"].sum()).reset_index()
line_mes_ent_df['fluxo'] = 'entrada'

# 4) Grafico de linhas das saídas por mes
filtered_date_sai_df = filtered_date.query('fluxo == "saida"')
line_mes_sai_df = pd.DataFrame(filtered_date_sai_df.groupby(df["mes_ano"])["R$_abs"].sum()).reset_index()
line_mes_sai_df['fluxo'] = 'saida'
# Une dados de entrada e saida
line_mes_ent_sai_df = pd.concat([line_mes_ent_df,line_mes_sai_df])

# 5) Grafico de barras - classificação no período
bar_classif_rec_df = filtered_df.groupby(by = ["classificacao"], as_index = False)["R$"].\
              sum().sort_values('R$',ascending=False)

# 6) Grafico de linhas - classificação por mes
line_mesclassif_rec_df = pd.DataFrame(filtered_df[["mes_ano",'classificacao','R$']].\
                     groupby(by=["mes_ano",'classificacao']).sum()).reset_index()

# ==> Arquivo de emprestimos
# 7) Grafico de linhas da evolução saldo empréstimos por mês
line_mes_rec_df_emp = pd.DataFrame(filtered_emp_date.groupby("mes_ano")["R$"].sum()).reset_index()


#===============================================
# STREAMLIT LAYOUT DE PAGINA
#===============================================
#col1,col2 = st.columns((2), gap='medium')
#col3,col4 = st.columns((2))

# ==> Visão geral - afetada somente pelo primeiro filtro da aba lateral
st.write(' ====================================================')
st.write("==> Visão geral no Período Selecionado")
st.write(' ====================================================')

st.write(' ====================================================')
st.write("==> Usando Plotly Express")
st.write(' ====================================================')
 
with st.container(border=True):
    # Grafico 1
    fig1 = px.bar(bar_fluxo_rec_pos_df, x = "fluxo", y = "R$_abs", text = ['${:,.2f}'.format(x) \
                for x in bar_fluxo_rec_pos_df["R$_abs"]],template = "seaborn")
    fig1.update_traces(marker_color=['green', 'red'])
    # Grafico 2
    x_str = line_mes_rec_df['mes_ano'].dt.strftime("%m/%Y")
    fig2 = px.line(line_mes_rec_df, x = x_str, y="R$", markers=True, labels = {"mes_ano": "Mês_ano"},\
                template="seaborn")
    #            height=300, width = 500,template="seaborn")
    # Definindo marker
    fig2.update_traces(marker=dict(size=5, symbol='circle'))

    # Criando figura com 2 graficos
    fig = make_subplots(rows=1, cols=2)
    # Adicionando os gráficos Plotly Express ao layout de subplot
    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)
        
    for trace in fig2.data:
        fig.add_trace(trace, row=1, col=2)

    # ========================================================
    # Acoes para todos os graficos
    # ========================================================
    # Adicionando títulos individuais para cada subplot
    titles = ["<b>Fluxo acumulado no período</b>", "<b>Saldo por mês</b>"]
    positions = [(0.07, 1.1), (0.85, 1.1)]  # Ajuste as posições conforme necessário

    annotations = [
        dict(
            x=position[0], y=position[1], xref="paper", yref="paper",
            text=title, showarrow=False, font=dict(size=16)
        ) for title, position in zip(titles, positions)
    ]

    fig.update_layout(annotations=annotations)

    #
    fig.update_yaxes(title_text="R$", row=1, col=1)
    fig.update_yaxes(title_text="R$", row=1, col=2)
    st.plotly_chart(fig,use_container_width=True) 

# ========================================================
# Explicacao graficos 1 e 2
# ========================================================
with st.container(border=True):
    cool1, cool2 = st.columns(2)
    # Mensagem 1
    with cool1:
        st.info("Apresenta a soma de entradas(positivo) e saídas(negativo) \
                no período selecionado")
    # Mensagem 2
    with cool2:
        st.info("Apresenta a diferença entre entradas e saídas ao longo de cada mês. \
                O objetivo é sempre estar com este valor positivo.")


 
with st.container(border=True):
    # Grafico 1
    x_str1 = line_mes_rec_df_emp.mes_ano.dt.strftime("%m/%Y")
    fig1 = px.line(line_mes_rec_df_emp, x = x_str1, y="R$", labels = {"mes_ano": "Mês_ano"},\
                    markers=True,template="seaborn")
    # Definindo marker
    fig1.update_traces(marker=dict(size=5, symbol='circle'))


    ## Grafico 2
    x_str2 = line_mes_ent_sai_df['mes_ano'].dt.strftime("%m/%Y")
    fig2 = px.line(line_mes_ent_sai_df, x= x_str2,y="R$_abs",markers=True,color="fluxo",
                        color_discrete_map = {
                            'entrada': 'green',
                            'saida':'red'
                        })
    # Definindo marker
    fig2.update_traces(marker=dict(size=5, symbol='circle'))

    # Criando sub-plots
    fig = make_subplots(rows=1, cols=2)

    # Adicionando os gráficos Plotly Express ao layout de subplot
    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)
        
    for trace in fig2.data:
        fig.add_trace(trace, row=1, col=2)


    # ========================================================
    # Acoes para todos os graficos
    # ========================================================
    # Adicionando títulos individuais para cada subplot
    titles = ["<b>Saldo empréstimos por mês</b>", "<b>Entradas/Saídas por mês</b>"]
    positions = [(0.07, 1.1), (0.93, 1.1)]  # Ajuste as posições conforme necessário

    annotations = [
        dict(
            x=position[0], y=position[1], xref="paper", yref="paper",
            text=title, showarrow=False, font=dict(size=16)
        ) for title, position in zip(titles, positions)
    ]

    fig.update_layout(annotations=annotations)

    #
    fig.update_yaxes(title_text="R$", row=1, col=1)
    fig.update_yaxes(title_text="R$", row=1, col=2)
    st.plotly_chart(fig,use_container_width=True)

# ========================================================
# Explicacao graficos 3 e 4
# ========================================================
with st.container(border=True):
    cool1, cool2 = st.columns(2)
    # Mensagem 1
    with cool1:
        st.info("Apresenta o comportamento dos empréstimos por mês. Os empréstimos tem juros \
            associados e portanto impactam na despesa financeira. É desejável ver o valor diminuindo no tempo")
    # Mensagem 2
    with cool2:
        st.info("Apresenta o detalhamento das entradas e saídas ao longo de cada mês. \
                    O objetivo é sempre estar com o gráfico de entrada superior a \
                        saída. A diferença entre estes gráficos é que produz o saldo por mês.")


st.write(' ====================================================')
st.write("==> Detalhamento")
st.write(' ====================================================')

with st.container(border=True):
    st.subheader("Classificação no período")
    fig = px.bar(bar_classif_rec_df, x = "classificacao", y = "R$", 
                     text = ['${:,.2f}'.format(x) for x in bar_classif_rec_df["R$"]],
                    template = "seaborn")
    #fig.update_layout(height=400,margin=dict(l=50, r=10, t=100, b=10, pad=8))
    st.plotly_chart(fig,use_container_width=True)
    st.info("Neste gráfico  de barras importante observar que as receitas são colocadas  \
                como positivas e as saídas como negativas. Importante analisar entradas e saídas \
                    separadamente usando a seleção na barra lateral na coluna fluxo.")

 
with st.container(border=True):
    st.subheader("Classificação por mês")
    x_str = line_mesclassif_rec_df['mes_ano'].dt.strftime("%m/%Y")
    fig = px.line(line_mesclassif_rec_df, x = x_str, y='R$', color='classificacao',\
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
  




st.write(' ====================================================')
st.write("==> Usando Plotly")
st.write(' ====================================================')

with st.container(border=True):
    fig = make_subplots(rows=1, cols=2)

    # ROW,COL = (1,1)
    x_axis = bar_fluxo_rec_pos_df['fluxo']
    y_axis = bar_fluxo_rec_pos_df['R$_abs']
    colors = ['green','red']

    fig.add_trace(go.Bar(x= x_axis, y= y_axis, marker_color=colors,showlegend=False,
                    text=['R${:,.2f}'.format(x) for x in bar_fluxo_rec_pos_df['R$_abs']]),row=1, col=1)
 
    # ROW,COL = (1,2)
    x_axis = line_mes_rec_df['mes_ano']
    y_axis = line_mes_rec_df['R$']
    x_axis_str = line_mes_rec_df['mes_ano'].dt.strftime("%m/%Y")

    fig.add_trace(go.Scatter(x= x_axis_str, y= y_axis,mode='lines+markers',showlegend=False,
                            name = 'saldo',line = dict(color='blue')),row=1, col=2)


    # ========================================================
    # Acoes para todos os graficos
    # ========================================================
    ## Adicionando títulos individuais para cada subplot
    titles = ["Fluxo acumulado no período", "Saldo por mês"] 
    positions = [(0.07, 1.1), (0.90, 1.1)]  # Ajuste as posições conforme necessário
    annotations = [
        dict(
            x=position[0], y=position[1], xref="paper", yref="paper",
            text=title, showarrow=False, font=dict(size=16)
        ) for title, position in zip(titles, positions)
    ]

    fig.update_layout(annotations=annotations)

    #
    fig.update_yaxes(title_text="R$", row=1, col=1)
    #fig.update_yaxes(title_text="R$", row=1, col=2)
    st.plotly_chart(fig,use_container_width=True)   

# ========================================================
# Explicacao graficos 1 e 2
# ========================================================
with st.container(border=True):
    cool1, cool2 = st.columns(2)
    # Mensagem 1
    with cool1:
        st.info("Apresenta a soma de entradas(positivo) e saídas(negativo) \
                no período selecionado")
    # Mensagem 2
    with cool2:
        st.info("Apresenta a diferença entre entradas e saídas ao longo de cada mês. \
                O objetivo é sempre estar com este valor positivo.")


with st.container(border=True):
    fig = make_subplots(rows=1, cols=2)
    
    # ROW,COL = (1,1)
    x_axis = line_mes_rec_df_emp['mes_ano']
    y_axis = line_mes_rec_df_emp['R$']
    x_axis_str = line_mes_rec_df_emp['mes_ano'].dt.strftime("%m/%Y")

    fig.add_trace(go.Scatter(x= x_axis_str, y= y_axis,mode='lines+markers',showlegend=False,
                            name = 'empréstimos',line = dict(color='blue')),row=1, col=1)

    # ROW,COL = (1,2)
    x_axis1 = line_mes_ent_df['mes_ano']
    x_axis1_str = line_mes_ent_df['mes_ano'].dt.strftime("%m/%Y")
    y_axis1 = line_mes_ent_df['R$_abs']

    x_axis2 = line_mes_sai_df['mes_ano']
    x_axis2_str = line_mes_sai_df['mes_ano'].dt.strftime("%m/%Y")
    y_axis2 = line_mes_sai_df['R$_abs']


    fig.add_trace(go.Scatter(x= x_axis1_str, y= y_axis1,mode='lines+markers', 
                            name = 'entradas',line = dict(color='green')),row=1, col=2)
    fig.add_trace(go.Scatter(x= x_axis2_str, y= y_axis2,mode='lines+markers', 
                            name = 'saídas',line = dict(color='red')),row=1, col=2)

    # ========================================================
    # Acoes para todos os graficos
    # ========================================================

    # Adicionando títulos individuais para cada subplot
    titles = ["Saldo empréstimos por mês", "Entradas/Saídas por mês"]
    positions = [(0.07, 1.1), (0.90, 1.1)]   # Ajuste as posições conforme necessário

    annotations = [
        dict(
            x=position[0], y=position[1], xref="paper", yref="paper",
            text=title, showarrow=False, font=dict(size=16)
        ) for title, position in zip(titles, positions)
    ]

    fig.update_layout(annotations=annotations)

    fig.update_yaxes(title_text="R$", row=1, col=1)
    #fig.update_yaxes(title_text="R$", row=1, col=2)
    st.plotly_chart(fig,use_container_width=True)

# ========================================================
# Explicacao graficos 3 e 4
# ========================================================
with st.container(border=True):
    cool1, cool2 = st.columns(2)
    # Mensagem 1
    with cool1:
        st.info("Apresenta o comportamento dos empréstimos por mês. Os empréstimos tem juros \
            associados e portanto impactam na despesa financeira. É desejável ver o valor diminuindo no tempo")
    # Mensagem 2
    with cool2:
        st.info("Apresenta o detalhamento das entradas e saídas ao longo de cada mês. \
                    O objetivo é sempre estar com o gráfico de entrada superior a \
                        saída. A diferença entre estes gráficos é que produz o saldo por mês.")

