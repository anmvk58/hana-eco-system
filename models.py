from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, func


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
    phone_number = Column(String)


class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))


class Shippers(Base):
    __tablename__ = 'shipper'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    full_name = Column(String)
    phone = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    create_at = Column(TIMESTAMP, server_default=func.now())

class Bills(Base):
    __tablename__ = 'bills'

    bill_code = Column(String, primary_key=True, index=True)
    group_bill = Column(String)
    cust_name = Column(String)
    cust_phone = Column(String)
    cust_address = Column(String)
    amount = Column(Integer, nullable=False)
    is_transfer = Column(Boolean, default=False)
    shipper_id = Column(Integer)
    shipper_name = Column(String)
    business_date = Column(Integer)
    create_at = Column(TIMESTAMP, server_default=func.now())