import os
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST_PROD')
DB_PORT = os.getenv('DB_PORT_PROD')
DB_NAME = os.getenv('DB_NAME_PROD')
DB_USER = os.getenv('DB_USER_PROD')
DB_PASS = os.getenv('DB_PASS_PROD')
DB_SCHEMA = os.getenv('DB_SCHEMA_PROD', 'public')

SYMBOLS = ['CL=F', 'GC=F', 'SI=F', 'NG=F', 'HG=F']


def fetch_commodities(symbols: list, period: str = '6mo') -> pd.DataFrame:
    frames = []
    for symbol in symbols:
        hist = yf.Ticker(symbol).history(period=period)[['Close']].reset_index()
        hist['simbolo'] = symbol
        frames.append(hist)
    return pd.concat(frames, ignore_index=True)


def load_to_postgres(df: pd.DataFrame, engine) -> None:
    df.to_sql('commodities', engine, schema=DB_SCHEMA, if_exists='replace', index=False)
    print(f"Carregados {len(df)} registros na tabela {DB_SCHEMA}.commodities.")


if __name__ == '__main__':
    missing = [k for k, v in {
        'DB_HOST_PROD': DB_HOST, 'DB_PORT_PROD': DB_PORT, 'DB_NAME_PROD': DB_NAME,
        'DB_USER_PROD': DB_USER, 'DB_PASS_PROD': DB_PASS,
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Variáveis de ambiente ausentes no .env: {', '.join(missing)}")

    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    df = fetch_commodities(SYMBOLS)
    load_to_postgres(df, engine)
