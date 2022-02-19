import geopandas
import streamlit as st
import pandas    as pd
import numpy     as np
import folium
# import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib import gridspec
from streamlit_folium import folium_static
from folium.plugins   import MarkerCluster



st.set_page_config( layout='wide' )

@st.cache( allow_output_mutation=True )
def get_data( path ):
    data = pd.read_csv( path )

    return data

@st.cache( allow_output_mutation=True )
def get_geofile( url ):
    geofile = geopandas.read_file( url )

    return geofile

# get data
# path = 'C:\\Users\\SERVIDOR\\Desktop\\x\\mega\\1_zero_ao_ds\\módulo_8\\kc_house_data.csv'
path = 'C:\\Users\\caixa\\Desktop\\kc_house_data.csv'
data = get_data( path )

# get geofile
url = 'https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'
geofile = get_geofile( url )


# add new features
data['date'] = pd.to_datetime( data['date'], format='%Y-%m-%d' )

# =======================
# Data Overview
# =======================
# f_attributes = st.sidebar.multiselect( 'Enter columns', data.columns )
#
# f_zipcode = st.sidebar.multiselect(
#     'Enter zipcode',
#     data['zipcode'].unique() )
#
# st.title( 'Data Overview' )
#
# if ( f_zipcode != [] ) & ( f_attributes != [] ):
#     data = data.loc[data['zipcode'].isin( f_zipcode ), f_attributes]
#
# elif ( f_zipcode != [] ) & ( f_attributes == [] ):
#     data = data.loc[data['zipcode'].isin( f_zipcode ), :]
#
# # elif ( f_zipcode == [] ) & ( f_attributes != [] ):
# #     data = data.loc[:, f_attributes]
#
# elif (f_zipcode == []) & (f_attributes != []):
#     data = data.loc[:, f_attributes]
#
# else:
#     data = data.copy()
#
# st.dataframe( data )
#
# c1, c2 = st.columns((1, 1) )

#=============================================================================
#TABELA DE COMPRA
#=============================================================================

#criando uma coluna com o preço mediano por região----------------
df=data[['zipcode','price']].groupby(['zipcode']).median().reset_index()
data=pd.merge(data,df,on='zipcode',how='inner')

# # renomeando colunas (antiga e recém criada)-----------------------
data= data.rename(columns={'price_x':'price', 'price_y': 'zip_mprice'})


# #CRIANDO UMA TABELA DE RECOMENDAÇÃO DE COMPRA

def status(price,zip_mprice,condition,waterfront):
    status='0'
    if (price < zip_mprice) & (condition > 4):
        status='buy'
    else:
        status='not_buy'
    return status


data['status']= data[['price','zip_mprice','condition','waterfront']].apply(lambda x : status(*x),axis=1)


# TABELA DE RECOMENDAÇÃO DE COMPRA-----------------------------------------------------
dfbuy=data.loc[data['status']=='buy']


# removendo colunas
dfbuy=dfbuy.drop(['date','condition', 'grade','yr_renovated','yr_built','view','lat', 'long', 'sqft_living15', 'sqft_lot15', 'zip_mprice', 'status'],axis=1)

# reorganizando colunas
dfbuy=dfbuy[['id','zipcode', 'price','floors', 'bedrooms', 'bathrooms', 'waterfront','sqft_lot', 'sqft_living','sqft_basement']]


dfbuy['price']=dfbuy['price'].astype('int')
dfbuy['floors']=dfbuy['floors'].astype('str')
dfbuy['bathrooms']=dfbuy['bathrooms'].astype('str')
dfbuy['bedrooms']=dfbuy['bedrooms'].astype('str')
dfbuy['waterfront']=dfbuy['waterfront'].astype('str')


# dfbuy['bathrooms']=dfbuy['bathrooms'].astype('int')



#TABELA DE VENDA--------------------------------------------------------------------------------

# criando uma coluna com os meses e dias-----------------------------------
data['month'] = data['date'].astype('str').str[4:]

# removendo os hífens
data['month'] = data['month'].replace('-', '', regex=True).astype(str)



# criando uma coluna com as estações-------------------------------
data['seasons'] = data['month'].apply(lambda x: 'winter' if (x >= '1221') & (x <= '1231') else
'winter' if (x >= '0101') & (x <= '0320') else
'spring' if (x >= '0321') & (x <= '0621') else
'summer' if (x >= '0622') & (x <= '0922') else
'fall')




# # criando uma tabela com o preço mediano por região e estação----------
df = data[['zipcode', 'seasons', 'price']].groupby(['seasons']).median().reset_index()
data = pd.merge(data, df, on='seasons', how='inner')

# # renomeando colunas recém criadas-----------------------------------
data = data.rename(
    columns={'price_y': 'zip_season_mprice', 'price_x': 'price', 'zipcode_x': 'zipcode', 'seasons_byzip': 'seasons'})
# # # removendo colunas desnecessárias---------------------------------
data = data.drop(['month', 'zipcode_y'], axis=1)


# # CRIANDO DUAS COLUNAS COM AS VARIAÇÕES DOS VALORES DE VENDA----------------

def sell_price10(status, price, zip_season_mprice):
    if (status == 'buy') & (price > zip_season_mprice):
        sell_price10 = price * 1.1

    else:
        sell_price10 = 0

    return sell_price10


data['sell_price10%'] = data[['status', 'price', 'zip_season_mprice']].apply(lambda x: sell_price10(*x), axis=1)


def sell_price30(status, price, zip_season_mprice):
    if (status == 'buy') & (price < zip_season_mprice):
        sell_price30 = price * 1.3

    else:
        sell_price30 = '0'

    return sell_price30


data['sell_price30%'] = data[['status', 'price', 'zip_season_mprice']].apply(lambda x: sell_price30(*x), axis=1)


# TABELAS DE RECOMENDAÇÃO DE VENDA

dfs30 = data.loc[data['status'] == 'buy']
dfs30 = dfs30.drop(['date',
                    'condition', 'grade',
                    'yr_renovated', 'yr_built', 'view',
                    'lat', 'long', 'sqft_living15', 'sqft_lot15', 'zip_mprice', 'status', 'sell_price10%'], axis=1)

dfs30 = dfs30[['id', 'zipcode', 'price', 'sell_price30%', 'floors', 'bedrooms', 'bathrooms', 'waterfront', 'sqft_lot',
               'sqft_living', 'sqft_basement']]

dfs30['sell_price30%']=dfs30['sell_price30%'].astype('float64')
dfs30=dfs30.loc[dfs30['sell_price30%']>1]

dfs30['price']=dfs30['price'].astype('int')
dfs30['floors']=dfs30['floors'].astype('str')
dfs30['bathrooms']=dfs30['bathrooms'].astype('str')
dfs30['bedrooms']=dfs30['bedrooms'].astype('str')
dfs30['waterfront']=dfs30['waterfront'].astype('str')




dfs10 = data.loc[data['status'] == 'buy']
dfs10 = dfs10.drop(['date',
                    'condition', 'grade',
                    'yr_renovated', 'yr_built', 'view',
                    'lat', 'long', 'sqft_living15', 'sqft_lot15', 'zip_mprice', 'sell_price30%', 'status',
                    'waterfront'], axis=1)

dfs10 = dfs10[['id', 'zipcode', 'price', 'sell_price10%', 'floors', 'bedrooms', 'bathrooms', 'sqft_lot', 'sqft_living',
               'sqft_basement']]
dfs10 = dfs10.loc[dfs10['sell_price10%'] > 0]

dfs10['price']=dfs10['price'].astype('int')
dfs10['floors']=dfs10['floors'].astype('str')
dfs10['bathrooms']=dfs10['bathrooms'].astype('str')
dfs10['bedrooms']=dfs10['bedrooms'].astype('str')
# dfs10['waterfront']=dfs10['waterfront'].astype('str')

# =======================================================================================================
# PLOTANDO NO STREAMLIT

st.title( 'Imóveis para comprar' )

# f_buys = st.sidebar.multiselect( 'Enter columns', dfbuy.columns )
f_zipcode = st.sidebar.multiselect('Enter zipcode',dfbuy['zipcode'].unique() )

if  f_zipcode != [] :
    dfbuy =dfbuy.loc[dfbuy['zipcode'].isin( f_zipcode )]

else:
    dfbuy = dfbuy.copy()

st.dataframe(dfbuy.style.format(subset=[ 'price'], formatter="{:,.2f}"))



st.title( 'Imóveis para vender após compra (10% de lucro)' )

# f_sell10 = st.sidebar.multiselect( 'Enter columns', dfs10.columns )
f_zipcodes1 = st.sidebar.multiselect('Enter zipcode',dfs10['zipcode'].unique() )

if  f_zipcodes1 != []  :
    dfs10 =dfs10.loc[dfs10['zipcode'].isin( f_zipcodes1 ) ]

# elif ( f_zipcodes1 != [] ) & (f_sell10 == [] ):
#     dfs10 = dfs10.loc[dfs10['zipcode'].isin( f_zipcodes1 ), :]
#
# elif (f_zipcodes1 == []) & (f_sell10 != []):
#     dfs10= dfs10.loc[:, f_sell10]

else:
    dfs10 = dfs10.copy()

st.dataframe(dfs10.style.format(subset=['price','sell_price10%'], formatter="{:,.2f}"))




st.title( 'Imóveis para vender após compra (30% de lucro)' )

# f_sell30 = st.sidebar.multiselect( 'Enter columns', dfs30.columns )
f_zipcodes3 = st.sidebar.multiselect('Enter zipcode',dfs30['zipcode'].unique() )

if  f_zipcodes3 != [] :
    dfs30 =dfs30.loc[dfs30['zipcode'].isin( f_zipcodes3 )]

# elif ( f_zipcodes3 != [] ) & (f_sell30 == [] ):
#     dfs30 = dfs30.loc[dfs30['zipcode'].isin( f_zipcodes3 ), :]
#
# elif (f_zipcodes3 == []) & (f_sell30 != []):
#     dfs10= dfs30.loc[:, f_sell30]

else:
    dfs30 = dfs30.copy()

st.dataframe(dfs30.style.format(subset=[ 'price','sell_price30%'], formatter="{:,.2f}"))




#================================================================================================================
# st.title( 'Imóveis para vender após compra ' )
# c1,c2=st.columns((1,1))
#
# c1.header('10% de lucro')
# c1.dataframe(dfs10, height=400,width=400)
#
# f_sell10 = st.sidebar.multiselect( 'Enter columns', dfs10.columns )
# f_zipcodes1 = st.sidebar.multiselect('Enter zipcode',dfs10['zipcode'].unique() )
#
# if ( f_zipcodes1 != [] ) & ( f_sell10 != [] ):
#     dfs10 =dfs10.loc[dfs10['zipcode'].isin( f_zipcodes1 ), f_sell10]
#
# elif ( f_zipcodes1 != [] ) & (f_sell10 == [] ):
#     dfs10 = dfs10.loc[dfs10['zipcode'].isin( f_zipcodes1 ), :]
#
# elif (f_zipcodes1 == []) & (f_sell10 != []):
#     dfs10= dfs10.loc[:, f_sell10]
#
# else:
#     dfs10 = dfs10.copy()
#
#
# c2.header('30% de lucro')
# c2.dataframe(dfs30,height=400,width=400)
#================================================================================================================

# push code ubuntu teste
