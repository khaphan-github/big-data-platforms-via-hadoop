from sqlalchemy import create_engine

DB_URL = "mysql+pymysql://root:rss_password@127.0.0.1:3308/rss_ingest"

print("DATABASE_URL =", DB_URL)
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)