from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = 'sqlite:///./hana_app.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == '__main__':
    import uuid


    def generate_unique_uuid():
        return str(uuid.uuid4())[:6].upper()  # Cắt lấy 6 ký tự đầu


    print(generate_unique_uuid())
