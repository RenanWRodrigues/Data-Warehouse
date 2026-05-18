import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST_PROD')
DB_PORT = os.getenv('DB_PORT_PROD')
DB_NAME = os.getenv('DB_NAME_PROD')
DB_USER = os.getenv('DB_USER_PROD')
DB_PASS = os.getenv('DB_PASS_PROD')
DB_SCHEMA = os.getenv('DB_SCHEMA_PROD')

missing = [k for k, v in {
    'DB_HOST_PROD': DB_HOST, 'DB_PORT_PROD': DB_PORT, 'DB_NAME_PROD': DB_NAME,
    'DB_USER_PROD': DB_USER, 'DB_PASS_PROD': DB_PASS, 'DB_SCHEMA_PROD': DB_SCHEMA,
}.items() if not v]

if missing:
    raise EnvironmentError(f"Variáveis de ambiente ausentes no .env: {', '.join(missing)}")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)


@st.cache_data(ttl=300)
def get_data() -> pd.DataFrame:
    query = f"""
    SELECT
        data,
        simbolo,
        valor_fechamento,
        acao,
        quantidade,
        valor,
        ganho
    FROM
        {DB_SCHEMA}.dm_commodities
    ORDER BY data;
    """
    return pd.read_sql(query, engine)


st.set_page_config(page_title='Dashboard de Commodities', layout='wide')
st.title('Dashboard de Commodities')

df = get_data()
df['data'] = pd.to_datetime(df['data'])

with st.sidebar:
    st.header('Filtros')
    symbols = st.multiselect(
        'Commodities',
        options=sorted(df['simbolo'].unique()),
        default=sorted(df['simbolo'].unique()),
    )
    min_date = df['data'].min().date()
    max_date = df['data'].max().date()
    date_range = st.date_input(
        'Período',
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

if len(date_range) == 2:
    start, end = date_range
    df_filtered = df[
        df['simbolo'].isin(symbols) &
        (df['data'].dt.date >= start) &
        (df['data'].dt.date <= end)
    ]
else:
    df_filtered = df[df['simbolo'].isin(symbols)]

col1, col2, col3, col4 = st.columns(4)
col1.metric('Ganho Total', f"$ {df_filtered['ganho'].sum():,.2f}")
col2.metric('Volume Total', f"$ {df_filtered['valor'].sum():,.2f}")
col3.metric('Transações', len(df_filtered))
col4.metric('Commodities', df_filtered['simbolo'].nunique())

st.divider()

st.subheader('Evolução do Preço de Fechamento')
price_pivot = (
    df_filtered[['data', 'simbolo', 'valor_fechamento']]
    .drop_duplicates()
    .pivot(index='data', columns='simbolo', values='valor_fechamento')
)
st.line_chart(price_pivot)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader('Ganho por Commodity')
    ganho_por_simbolo = (
        df_filtered.groupby('simbolo')['ganho']
        .sum()
        .reset_index()
        .set_index('simbolo')
    )
    st.bar_chart(ganho_por_simbolo)

with col_right:
    st.subheader('Volume por Commodity')
    volume_por_simbolo = (
        df_filtered.groupby('simbolo')['valor']
        .sum()
        .reset_index()
        .set_index('simbolo')
    )
    st.bar_chart(volume_por_simbolo)

st.divider()
st.subheader('Dados Detalhados')
st.dataframe(df_filtered, use_container_width=True)
