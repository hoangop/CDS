from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Lấy URL từ biến môi trường hoặc dùng default local docker
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/cds_db" # URL trong mạng Docker
)

# Nếu chạy local ngoài docker (để test):
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cds_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

