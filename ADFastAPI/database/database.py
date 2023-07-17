from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import contextlib

SQLALCHEMY_DATABASE_URL = 'postgresql+psycopg2://user:password@ad_db:5432/ad_db'
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextlib.contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()