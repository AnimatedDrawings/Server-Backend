from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy import text

ad_db_url = 'postgresql+psycopg2://user:password@localhost:5432/ad_db'
engine = create_engine(ad_db_url)

db = scoped_session(sessionmaker(bind=engine))

result = db.execute(text("SELECT 1"))
print(result.fetchone())