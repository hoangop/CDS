from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Lấy URL từ biến môi trường hoặc dùng default local docker
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/cds_db" # URL trong mạng Docker
)

# Hỗ trợ Cloud SQL với Unix socket
# Nếu DATABASE_URL chứa /cloudsql/, sử dụng psycopg2 driver (tốt hơn pg8000 cho Unix socket)
if SQLALCHEMY_DATABASE_URL and "/cloudsql/" in SQLALCHEMY_DATABASE_URL:
    # Cloud SQL connection qua Unix socket - psycopg2 hỗ trợ tốt hơn
    # Không cần thay đổi driver vì psycopg2 là default cho postgresql://
    pass

# Tạo engine với connection pooling cho production
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600    # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

