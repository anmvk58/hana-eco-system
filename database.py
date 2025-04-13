from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base

# SQLALCHEMY_DATABASE_URL = 'sqlite:///./hana_app.db'
DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/hanadb"

# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()