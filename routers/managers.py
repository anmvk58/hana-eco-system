from datetime import datetime
from http.client import HTTPResponse

from sqlalchemy.exc import IntegrityError
from typing import Annotated, Optional
from pydantic import BaseModel, Field, computed_field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from models import Bills, Shippers, UserRequest, Users
from database import get_db
from utils.date_utils import get_current_date
from .auth import get_current_user
import uuid

router = APIRouter(
    prefix='/managers',
    tags=['managers']
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class CreateShipperForm(BaseModel):
    user_id: str = Field(description='ID của user hệ thống')
    username: str = Field(description='Username của user (lấy từ hệ thống)')
    full_name: str = Field(description='Họ tên của user (lấy từ hệ thống)')
    phone: str = Field(description='SĐT của shipper')
    type: str = Field(description='Loại Shipper: FULL_TIME, PART_TIME, EXTERNAL')


# Api cho phép manager tạo tài khoản shipper
@router.post("/create-shipper", status_code=status.HTTP_201_CREATED)
async def create_shipper_account(user: user_dependency,
                                 db: db_dependency,
                                 create_shipper_form: CreateShipperForm):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    # Validate User_id
    try:
        # Check validate user_id
        user_model = db.query(Users).filter(Users.id == create_shipper_form.user_id).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    if user_model is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User ID không hợp lệ')

    # Create a shipper account
    try:
        shipper_model = Shippers(**create_shipper_form.model_dump(), is_active=True)
        db.add(shipper_model)
        db.commit()
        return {"message": f"Tạo thành công shipper {create_shipper_form.full_name}"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Api list all user là Shipper trong hệ thống:
class UserOut(BaseModel):
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: Optional[str]
    phone_number: Optional[str]
    create_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}".strip()

    model_config = {
        "from_attributes": True
    }


@router.get("/list-all-users", status_code=status.HTTP_200_OK, response_model=list[UserOut])
async def get_all_users(user: user_dependency,
                        db: db_dependency,
                        type: str = None):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    try:
        if type is None:
            users_model = db.query(Users).filter(Users.is_active == True).all()
        else:
            users_model = db.query(Users).filter(Users.is_active == True, Users.role == type.upper()).all()
        return users_model
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


@router.get("/list-all-request", status_code=status.HTTP_200_OK)
async def get_all_request_by_status(user: user_dependency,
                                    db: db_dependency,
                                    from_date: int,
                                    to_date: int,
                                    request_status: str = None):
    # Authen
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    # Author
    print(user)
    # if user.get("user_role") not in ['MANAGER', 'ADMIN']:
    if user.get("user_role") != 'MANAGER' and user.get("user_role") != 'ADMIN':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Authorization Failed, Only for MANAGER role')

    # Main Logic
    try:
        if request_status is None:
            request_model = db.query(UserRequest).filter(UserRequest.business_date >= from_date,
                                                         UserRequest.business_date <= to_date).all()
        else:
            request_model = db.query(UserRequest).filter(UserRequest.business_date >= from_date,
                                                         UserRequest.business_date <= to_date,
                                                         UserRequest.status == request_status.upper()).all()
        return request_model
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")
