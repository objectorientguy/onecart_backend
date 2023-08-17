
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://onecart_user:wEKhTsHIj4DWVJQZd4Csl63URv2gbPcA@dpg-cjcvoufdb61s73ae8mkg-a.singapore-postgres.render.com/onecart"
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:9993@localhost/fastapi"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

