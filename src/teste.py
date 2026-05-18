import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST_PROD', 'localhost')
DB_PORT = os.getenv('DB_PORT_PROD', '5432')
DB_NAME = os.getenv('DB_NAME_PROD', 'dbsalesaovivo')
DB_USER = os.getenv('DB_USER_PROD', 'postgres')
DB_PASS = os.getenv('DB_PASS_PROD')

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine.connect()

print("Conectado!")
