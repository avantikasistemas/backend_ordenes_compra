import sqlalchemy
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

BASE = declarative_base() 
load_dotenv()

driver = os.getenv("DRIVER")
user = os.getenv("DB_USER")
passwd = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
trusted_connection = os.getenv("TRUST_CERTIFICATE")
encrypt = os.getenv("ENCRYPT")

connect_url = sqlalchemy.engine.url.URL(
    "mssql+pyodbc",
    username=user,
    password=passwd,
    host=host,
    port=int(port),
    database=db_name,
    query={
        "driver": driver, 
        "TrustServerCertificate": trusted_connection,
    }
)

engine = sqlalchemy.create_engine(connect_url, poolclass=NullPool)
session_maker = sessionmaker(bind=engine)
session = session_maker()
