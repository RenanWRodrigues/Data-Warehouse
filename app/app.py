import os
from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

# =========================================================
# CONFIGURAÇÕES INICIAIS
# =========================================================

st.set_page_config(
    page_title='Dashboard de Commodities',
    layout='wide'
)

st.title('📈 Dashboard de Commodities')

# =========================================================
# CARREGA VARIÁVEIS DE AMBIENTE
# =========================================================

load_dotenv(Path(__file__).parent.parent / ".env")

# =========================================================
# VARIÁVEIS DE AMBIENTE
# Compatível com:
# - VS Code (.env)
# - Streamlit Cloud (Secrets)
# =========================================================

def _get_secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except KeyError:
        return os.getenv(key)
    except Exception as e:
        st.warning(f"Erro ao acessar st.secrets['{key}']: {type(e).__name__}: {e}")
        return os.getenv(key)

DB_HOST = _get_secret("DB_HOST_PROD")
DB_PORT = _get_secret("DB_PORT_PROD")
DB_NAME = _get_secret("DB_NAME_PROD")
DB_USER = _get_secret("DB_USER_PROD")
DB_PASS = _get_secret("DB_PASS_PROD")
DB_SCHEMA = _get_secret("DB_SCHEMA_PROD")

# =========================================================
# VALIDAÇÃO DAS VARIÁVEIS
# =========================================================

try:
    st.write("🔍 DEBUG - Chaves em st.secrets:", list(st.secrets.keys()))
except Exception as e:
    st.write(f"🔍 DEBUG - st.secrets inacessível: {type(e).__name__}: {e}")

required_vars = {
    'DB_HOST_PROD': DB_HOST,
    'DB_PORT_PROD': DB_PORT,
    'DB_NAME_PROD': DB_NAME,
    'DB_USER_PROD': DB_USER,
    'DB_PASS_PROD': DB_PASS,
    'DB_SCHEMA_PROD': DB_SCHEMA,
}

missing = [
    key for key, value in required_vars.items()
    if not value
]

if missing:

    st.error(
        f"❌ Variáveis de ambiente ausentes: {', '.join(missing)}"
    )

    st.info(
        "Configure as variáveis no arquivo .env local "
        "ou em Advanced Settings > Secrets no Streamlit Cloud."
    )

    st.stop()

# =========================================================
# CONEXÃO COM POSTGRESQL
# =========================================================

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

try:

    engine = create_engine(DATABASE_URL)

except Exception as e:

    st.error(f"❌ Erro ao criar conexão com banco: {e}")

    st.stop()

# =========================================================
# FUNÇÃO DE CONSULTA
# =========================================================


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
    ORDER BY
        data;
    """

    try:

        df = pd.read_sql(query, engine)

        return df

    except Exception as e:

        st.error(f"❌ Erro ao consultar banco: {e}")

        st.stop()

# =========================================================
# CARREGA DADOS
# =========================================================


df = get_data()

# =========================================================
# VALIDAÇÃO DATAFRAME
# =========================================================

if df.empty:

    st.warning("⚠️ Nenhum dado encontrado.")

    st.stop()

# =========================================================
# CONVERSÃO DE DATA
# =========================================================

df['data'] = pd.to_datetime(df['data'])

# =========================================================
# SIDEBAR - FILTROS
# =========================================================

with st.sidebar:

    st.header('⚙️ Filtros')

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

# =========================================================
# FILTROS
# =========================================================

if len(date_range) == 2:

    start_date, end_date = date_range

    df_filtered = df[
        (df['simbolo'].isin(symbols)) &
        (df['data'].dt.date >= start_date) &
        (df['data'].dt.date <= end_date)
    ]

else:

    df_filtered = df[
        df['simbolo'].isin(symbols)
    ]

# =========================================================
# VALIDAÇÃO FILTRO
# =========================================================

if df_filtered.empty:

    st.warning(
        "⚠️ Nenhum dado encontrado para os filtros selecionados."
    )

    st.stop()

# =========================================================
# KPIs
# =========================================================

st.subheader('📊 Indicadores')

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    '💰 Ganho Total',
    f"$ {df_filtered['ganho'].sum():,.2f}"
)

col2.metric(
    '💵 Volume Total',
    f"$ {df_filtered['valor'].sum():,.2f}"
)

col3.metric(
    '📈 Transações',
    f"{len(df_filtered):,}"
)

col4.metric(
    '🏷️ Commodities',
    df_filtered['simbolo'].nunique()
)

# =========================================================
# GRÁFICO DE LINHA
# =========================================================

st.divider()

st.subheader('📉 Evolução do Preço de Fechamento')

price_pivot = (
    df_filtered[['data', 'simbolo', 'valor_fechamento']]
    .drop_duplicates()
    .pivot(
        index='data',
        columns='simbolo',
        values='valor_fechamento'
    )
)

st.line_chart(price_pivot)

# =========================================================
# GRÁFICOS LATERAIS
# =========================================================

col_left, col_right = st.columns(2)

# ---------------------------------------------------------
# GANHO POR COMMODITY
# ---------------------------------------------------------

with col_left:

    st.subheader('💹 Ganho por Commodity')

    ganho_por_simbolo = (
        df_filtered
        .groupby('simbolo')['ganho']
        .sum()
        .reset_index()
        .set_index('simbolo')
    )

    st.bar_chart(ganho_por_simbolo)

# ---------------------------------------------------------
# VOLUME POR COMMODITY
# ---------------------------------------------------------

with col_right:

    st.subheader('📦 Volume por Commodity')

    volume_por_simbolo = (
        df_filtered
        .groupby('simbolo')['valor']
        .sum()
        .reset_index()
        .set_index('simbolo')
    )

    st.bar_chart(volume_por_simbolo)

# =========================================================
# TABELA DETALHADA
# =========================================================

st.divider()

st.subheader('📋 Dados Detalhados')

st.dataframe(
    df_filtered,
    use_container_width=True
)

# =========================================================
# RODAPÉ
# =========================================================

st.divider()

st.caption(
    "Dashboard desenvolvido com Streamlit + PostgreSQL + SQLAlchemy"
)
