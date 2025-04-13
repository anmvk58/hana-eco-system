from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, func


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True)
    username = Column(String(50), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    hashed_password = Column(String(150))
    is_active = Column(Boolean, default=True)
    role = Column(String(50))
    phone_number = Column(String(15))
    create_at = Column(TIMESTAMP, server_default=func.now())


class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50))
    description = Column(String(254))
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))


class Shippers(Base):
    __tablename__ = 'shippers'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True)
    username = Column(String(50),  unique=True)
    full_name = Column(String(100))
    phone = Column(String(12), unique=True)
    type = Column(String(10))
    is_active = Column(Boolean, default=True)
    create_at = Column(TIMESTAMP, server_default=func.now())

class Bills(Base):
    __tablename__ = 'bills'

    bill_code = Column(String(13), primary_key=True, index=True)
    org_bill_code = Column(String(13), unique=True)
    group_bill = Column(String(20))
    cust_name = Column(String(100))
    cust_phone = Column(String(15))
    cust_address = Column(String(254))
    amount = Column(Integer, nullable=False)
    is_transfer = Column(Boolean, default=False)
    shipper_id = Column(Integer)
    shipper_name = Column(String(100))
    business_date = Column(Integer)
    status = Column(Integer)
    create_at = Column(TIMESTAMP, server_default=func.now())

class UserRequest(Base):
    __tablename__ = 'user_requests'

    request_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id_reqeust = Column(Integer, nullable=False)
    bill_code = Column(String(13))
    type = Column(String(50))
    content = Column(String(254))
    status = Column(String(10))
    user_id_approved = Column(Integer, nullable=True)
    reason = Column(String(254))
    business_date = Column(Integer)
    create_at = Column(TIMESTAMP, server_default=func.now())
    approved_at = Column(TIMESTAMP)