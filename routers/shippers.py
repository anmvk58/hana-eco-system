from sqlalchemy.exc import IntegrityError
from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from models import Bills, Shippers, UserRequest
from database import get_db
from utils.date_utils import get_current_date
from .auth import get_current_user


router = APIRouter(
    prefix='/shipper',
    tags=['shipper']
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Api cho phép shipper đánh dấu đơn hàng của bản thân thành ĐÃ CHUYỂN KHOẢN
@router.put("/mark-transfer/{bill_code}", status_code=status.HTTP_200_OK)
async def mark_transfer(user: user_dependency,
                        db: db_dependency,
                        bill_code: str):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        shipper = db.query(Shippers).filter(Shippers.user_id == user.get("id")).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    # Nếu user không phải là shipper:
    if shipper is None:
        raise HTTPException(status_code=403, detail='User need to be Shipper first')

    bill_model: Bills = db.query(Bills).filter(Bills.bill_code == bill_code, Bills.shipper_id == shipper.id).first()
    if bill_model is None:
        raise HTTPException(status_code=404, detail='Bill not found or You are not true shipper')

    if bill_model.status != 0:
        raise HTTPException(status_code=500, detail=f'Không thể sửa hóa đơn: {bill_code}. Đơn đã kiểm toán xong !')

    try:
        # Cập nhật hóa đơn thành đã chuyển khoản:
        bill_model.is_transfer = True

        db.add(bill_model)
        db.commit()
        return {"message": f"Đã update thành công {bill_code} thành [ĐÃ chuyển khoản!]"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Api cho phép shipper đánh dấu đơn hàng của bản thân thành CHƯA CHUYỂN KHOẢN
@router.put("/unmark-transfer/{bill_code}", status_code=status.HTTP_200_OK)
async def unmark_transfer(user: user_dependency,
                          db: db_dependency,
                          bill_code: str):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        shipper = db.query(Shippers).filter(Shippers.user_id == user.get("id")).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    # Nếu user không phải là shipper:
    if shipper is None:
        raise HTTPException(status_code=403, detail='User need to be Shipper first')

    bill_model: Bills = db.query(Bills).filter(Bills.bill_code == bill_code, Bills.shipper_id == shipper.id).first()
    if bill_model is None:
        raise HTTPException(status_code=404, detail='Bill not found or You are not true shipper')

    if bill_model.status != 0:
        raise HTTPException(status_code=403, detail=f'Không thể sửa hóa đơn: {bill_code}. Đơn đã kiểm toán xong !')

    try:
        # Cập nhật hóa đơn thành hủy chưa chuyển khoản:
        bill_model.is_transfer = False

        db.add(bill_model)
        db.commit()
        return {"message": f"Đã update thành công {bill_code} thành [CHƯA chuyển khoản!]"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Api cho phép shipper GỬI YÊU CẦU gỡ đơn hàng khỏi bản thân
@router.patch("/send-request/remove-bill/{bill_code}", status_code=status.HTTP_201_CREATED)
async def request_remove_bill(user: user_dependency,
                              db: db_dependency,
                              bill_code: str):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        shipper: Shippers = db.query(Shippers).filter(Shippers.user_id == user.get("id")).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    # Nếu user không phải là shipper:
    if shipper is None:
        raise HTTPException(status_code=403, detail='User need to be Shipper first')

    # Nếu không tồn tại bill_code hoặc user hiện tại không phải là shipper của đơn này
    bill_model: Bills = db.query(Bills).filter(Bills.bill_code == bill_code, Bills.shipper_id == shipper.id).first()
    if bill_model is None:
        raise HTTPException(status_code=404, detail='Bill not found or You are not true shipper')

    # Nếu hóa đơn đã được đánh dấu chốt xong thì cũng không được sửa
    if bill_model.status != 0:
        raise HTTPException(status_code=500, detail=f'Không thể sửa hóa đơn: {bill_code}. Đơn đã kiểm toán xong !')

    # Kiểm tra đã từng gửi request này chưa ?
    try:
        request: UserRequest = db.query(UserRequest).filter(UserRequest.user_id_reqeust == user.get("id"),
                                                            UserRequest.bill_code == bill_code,
                                                            UserRequest.type == 'REMOVE_BILL',
                                                            UserRequest.status != 'REJECT').first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")
    if request is not None:
        raise HTTPException(status_code=403, detail=f'Bạn đã gửi yêu cầu gỡ bỏ đơn {bill_code} này rồi !')

    # Cập tạo object_request_remove_bill:
    shipper_request = UserRequest(
        user_id_reqeust=user.get("id"),
        bill_code=bill_code,
        type='REMOVE_BILL',
        content=f'Shipper {shipper.full_name} đã yêu cầu gỡ bỏ đơn {bill_code}',
        status='CREATE',
        business_date=get_current_date()
    )

    try:
        db.add(shipper_request)
        db.commit()
        return {"message": f"Đã gủi yêu cầu gỡ bỏ đơn {bill_code} thành công !"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Api cho phép shipper GỬI YÊU CẦU điều chỉnh giá đơn hàng
class RequestChangeCOD(BaseModel):
    amount: int = Field(gt=0)

@router.post("/send-request/change-cod/{bill_code}", status_code=status.HTTP_200_OK)
async def request_change_cod(user: user_dependency,
                             db: db_dependency,
                             bill_code: str,
                             request_change_cod: RequestChangeCOD):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        shipper: Shippers = db.query(Shippers).filter(Shippers.user_id == user.get("id")).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    # Nếu user không phải là shipper:
    if shipper is None:
        raise HTTPException(status_code=403, detail='User need to be Shipper first')

    # Nếu không tồn tại bill_code hoặc user hiện tại không phải là shipper của đơn này
    bill_model: Bills = db.query(Bills).filter(Bills.bill_code == bill_code, Bills.shipper_id == shipper.id).first()
    if bill_model is None:
        raise HTTPException(status_code=404, detail='Bill not found or You are not true shipper')

    # Nếu hóa đơn đã được đánh dấu chốt xong thì cũng không được sửa
    if bill_model.status != 0:
        raise HTTPException(status_code=500, detail=f'Không thể sửa hóa đơn: {bill_code}. Đơn đã kiểm toán xong !')

    try:
        # Kiểm tra xem có spam request không ?
        request: UserRequest = db.query(UserRequest).filter(UserRequest.user_id_reqeust == user.get("id"),
                                                            UserRequest.bill_code == bill_code,
                                                            UserRequest.type == 'CHANGE_COD',
                                                            UserRequest.status != 'APPROVE').first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    if request is not None:
        raise HTTPException(status_code=403, detail=f'Bạn đã gửi yêu cầu thay đổi COD cho đơn {bill_code} rồi !')

    # Cập tạo object_request_remove_bill:
    shipper_request = UserRequest(
        user_id_reqeust=user.get("id"),
        bill_code=bill_code,
        type='CHANGE_COD',
        content=f'Shipper {shipper.full_name} đã yêu cầu điều chỉnh COD đơn {bill_code} từ {bill_model.amount} sang {request_change_cod.amount}',
        status='CREATE',
        business_date=get_current_date()
    )

    try:
        db.add(shipper_request)
        db.commit()
        return {"message": f"Đã gủi yêu cầu thay đổi COD đơn {bill_code} thành công !"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Api cho phép Shipper xem được danh sách các đơn hàng của mình
@router.get("/list-bills", status_code=status.HTTP_200_OK)
async def get_bills(user: user_dependency,
                             db: db_dependency,
                             from_date: int,
                             to_date: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        shipper: Shippers = db.query(Shippers).filter(Shippers.user_id == user.get("id")).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")

    # Nếu user không phải là shipper:
    if shipper is None:
        raise HTTPException(status_code=403, detail='User need to be Shipper first')

    try:
        # Query ra danh sach bills:
        bill_models = db.query(Bills).filter(Bills.shipper_id == shipper.id,
                                             Bills.business_date >= from_date,
                                             Bills.business_date <= to_date).all()
        if bill_models is None:
            raise HTTPException(status_code=404, detail='Bill not found or You are not true shipper')

        return {"message": f"Success", "data": bill_models}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")