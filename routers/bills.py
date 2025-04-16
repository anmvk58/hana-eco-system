from sqlalchemy.exc import IntegrityError
from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from models import Bills
from database import get_db
from utils.date_utils import get_current_date
from utils.string_utils import gen_group_bill_code, get_org_bill_code, extract_duplicate_bill
from .auth import get_current_user
from typing import Optional

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

class BillFilter(BaseModel):
    bill_code: Optional[str] = None
    cust_phone: Optional[str] = None
    cust_name: Optional[str] = None
    from_date: int
    to_date: int

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
                           business_date=get_current_date(),
                           status=0) for item in bills_request]

        db.add_all(new_bills)
        db.commit()
        return {"message": f"Đã tạo {len(new_bills)} bản ghi thành công!"}
    except IntegrityError as e:
        db.rollback()
        if "Duplicate entry" in str(e):
            dup_bill_code = extract_duplicate_bill('Duplicate entry ', str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'Bill {dup_bill_code} đã có shipper nhận, vui lòng gửi yêu cầu hủy trước')
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        # change id of shipper, name of shipper, tranfer status, amount
        bill_model.shipper_id = update_bill_request.shipper_id
        bill_model.shipper_name = update_bill_request.shipper_name
        bill_model.is_transfer = update_bill_request.is_transfer
        bill_model.amount = update_bill_request.amount

        db.add(bill_model)
        db.commit()
        return {"message": f"Đã update thành công {bill_code}!"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Lấy thông tin chi tiết của 1 bill
@router.get("/search-bill/{bill_code}", status_code=status.HTTP_200_OK)
async def get_bill_by_code(user: user_dependency,
                           db: db_dependency,
                           bill_code: str):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        bill_model = db.query(Bills).filter(Bills.bill_code == bill_code).first()

        return {
            "message": "Success",
            "data": bill_model
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


# Tìm kiếm thông tin của bills theo nhiều tiêu chí
@router.post("/search-bill", status_code=status.HTTP_200_OK)
async def get_bills_on_demand(user: user_dependency,
                           db: db_dependency,
                           bill_filter: BillFilter):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    try:
        query = db.query(Bills)

        if bill_filter.bill_code:
            query = query.filter(Bills.bill_code.ilike(bill_filter.bill_code))
        if bill_filter.cust_phone:
            query = query.filter(Bills.cust_phone == bill_filter.cust_phone)
        if bill_filter.cust_name:
            query = query.filter(Bills.cust_name.ilike(f"%{bill_filter.cust_name}%"))

        # add from_date and to_date
        query = query.filter(Bills.business_date >= bill_filter.from_date, Bills.business_date <= bill_filter.to_date )

        return {
            "message": "Success",
            "data": query.all()
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi server: {str(e)}")


