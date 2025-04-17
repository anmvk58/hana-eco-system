from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from starlette.responses import RedirectResponse

from models import Todos
from database import SessionLocal, get_db
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix='/common',
    tags=['common']
)

templates = Jinja2Templates(directory="templates")

### Pages ###
@router.get('/page-404')
def render_not_found_page(request: Request):
    return templates.TemplateResponse(name="common_page/page-404.html", request=request)


### Function ###
def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response