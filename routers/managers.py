from datetime import datetime
from http.client import HTTPResponse

from sqlalchemy.exc import IntegrityError
from typing import Annotated, Optional
from pydantic import BaseModel, Field, computed_field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from models import Bills, Shippers, UserRequest, Users
from database import get_db
from utils.date_utils import get_current_date
from .auth import get_current_user
from fastapi.templating import Jinja2Templates

from .common import redirect_to_login

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


class RequestForm(BaseModel):
    request_id: int = Field(description='ID của Request cần xử lý')
    reason: Optional[str] = Field(description='Lý do từ chối Request')


### Pages
templates = Jinja2Templates(directory="templates")


@router.get('/list-requests')
async def render_view_list_request_page(request: Request, db: db_dependency):
    # try:
    user = await get_current_user(request.cookies.get("access_token"))

    if user is None:
        return redirect_to_login()

    result = db.query(UserRequest, Users).join(Users).filter(UserRequest.business_date == get_current_date()).all()

    requests_model = [{
        "request_id": user_request.request_id,
        "bill_code": user_request.bill_code,
        "type": user_request.type,
        "content": user_request.content,
        "status": user_request.status,
        "approver": user_request.approver,
        "reason": user_request.reason,
        "create_at": user_request.create_at,
        "approved_at": user_request.approved_at,
    } for user_request, user in result]

    return templates.TemplateResponse(name="managers/list-requests.html",
                                      context={
                                          "request": request,
                                          "requests_model": requests_model,
                                          "user": user
                                      })


# except:
#     return redirect_to_login()


### Endpoints
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


# Api get danh sách các User của hệ thống đang active
@router.get("/list-all-users", status_code=status.HTTP_200_OK, response_model=list[UserOut])
async def get_all_users(user: user_dependency,
                        db: db_dependency,
                        user_type: str = None):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    try:
        if user_type is None:
            users_model = db.query(Users).filter(Users.is_active == True).all()
        else:
            users_model = db.query(Users).filter(Users.is_active == True, Users.role == user_type.upper()).all()
        return users_model
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Api get các request theo trạng thái mong muốn theo ngày business_date
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
    if user.get("user_role") not in ['MANAGER', 'ADMIN']:
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


# Api Reject yêu cầu của shipper:
@router.post("/reject-request", status_code=status.HTTP_200_OK)
async def get_all_request_by_status(user: user_dependency,
                                    db: db_dependency,
                                    reject_request_form: RequestForm):
    # Authen
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    # Author
    if user.get("user_role") not in ['MANAGER', 'ADMIN']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Authorization Failed, Only for MANAGER role')

    # Validate Request
    try:
        request_model = db.query(UserRequest).filter(UserRequest.request_id == reject_request_form.request_id,
                                                     UserRequest.status == 'CREATE').first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    if request_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Request không tồn tại hoặc đã được xử lý rồi')
    else:
        request_model.status = 'REJECT'
        request_model.user_id_approved = user.get("id")
        request_model.reason = reject_request_form.reason
        request_model.approved_at = datetime.now()

        try:
            db.add(request_model)
            db.commit()
            return {"message": f"Reject yêu cầu thành công"}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Api Accept yêu cầu của shipper:
@router.post("/accept-request", status_code=status.HTTP_200_OK)
async def get_all_request_by_status(user: user_dependency,
                                    db: db_dependency,
                                    accept_request_form: RequestForm):
    # Authen
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    # Author
    if user.get("user_role") not in ['MANAGER', 'ADMIN']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Authorization Failed, Only for MANAGER role')

    # Main Logic
    try:
        request_model = db.query(UserRequest).filter(UserRequest.request_id == accept_request_form.request_id,
                                                     UserRequest.status == 'CREATE').first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    if request_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Request không tồn tại hoặc đã được xử lý rồi')
    else:
        # Main Logic Here
        if request_model.type == 'REMOVE_BILL':
            # Xóa bill khỏi Bills Table luôn
            try:
                db.query(Bills).filter(Bills.bill_code == request_model.bill_code).delete()
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

        elif request_model.type == 'REMOVE_TRANSFER':
            # Đánh dấu không chuyển khoản
            try:
                bill_model = db.query(Bills).filter(Bills.bill_code == request_model.bill_code).first()
                bill_model.is_transfer = False
                db.add(bill_model)
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")
        elif request_model.type == 'CHANGE_COD':
            # Thay đổi COD đơn hàng
            try:
                new_amount = int(request_model.content.split(" ")[-1])
                bill_model = db.query(Bills).filter(Bills.bill_code == request_model.bill_code).first()
                bill_model.amount = new_amount
                db.add(bill_model)
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Loại yêu cầu không hợp lệ !')

        request_model.status = 'ACCEPT'
        request_model.user_id_approved = user.get("id")
        request_model.reason = accept_request_form.reason
        request_model.approved_at = datetime.now()

        try:
            db.add(request_model)
            db.commit()
            return {"message": f"Accept yêu cầu thành công"}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")
