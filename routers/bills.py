from sqlalchemy.exc import IntegrityError
from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from models import Bills
from database import get_db
from utils.date_utils import get_current_date
from utils.string_utils import gen_group_bill_code, get_org_bill_code
from .auth import get_current_user

router = APIRouter(
    prefix='/bills',
    tags=['bill']
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class BillsRequest(BaseModel):
    bill_code: str
    cust_name: str
    cust_phone: str
    cust_address: str
    amount: int = Field(gt=0)
    is_transfer: bool
    shipper_id: int = Field(gt=0)
    shipper_name: str


class UpdateBillRequest(BaseModel):
    amount: int = Field(gt=0)
    is_transfer: bool
    shipper_id: int = Field(gt=0)
    shipper_name: str

# Nhập hóa đơn theo batch là 1 danh sách các Bill Request
@router.post("/create-batch-bill", status_code=status.HTTP_201_CREATED)
async def create_batch_bill(user: user_dependency,
                            db: db_dependency,
                            bills_request: list[BillsRequest]):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    try:
        new_bills = [Bills(**item.model_dump(),
                           group_bill=gen_group_bill_code(),
                           org_bill_code=get_org_bill_code(item.bill_code),
                           business_date=get_current_date()) for item in bills_request]

        db.add_all(new_bills)
        db.commit()
        return {"message": f"Đã tạo {len(new_bills)} bản ghi thành công!"}
    except IntegrityError as e:
        db.rollback()
        if 'UNIQUE' in str(e):
            message = 'Đã có bill trùng bill với shipper khác'
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Update 1 Hóa đơn theo request Body = UpdateBillRequest ở trên
@router.put("/bill-exchange-shipper/{bill_code}", status_code=status.HTTP_204_NO_CONTENT)
async def update_bill(user: user_dependency,
                      db: db_dependency,
                      bill_code: str,
                      update_bill_request: UpdateBillRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        bill_model = db.query(Bills).filter(Bills.bill_code == bill_code).first()
        if bill_model is None:
            raise HTTPException(status_code=404, detail='Bill not found.')

        # update any attribute if you want:
        bill_model.shipper_id = update_bill_request.shipper_id

        db.add(bill_model)
        db.commit()
        return {"message": f"Đã update thành công {bill_code}!"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")
