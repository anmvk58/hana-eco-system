from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import models
from database import engine
from routers import auth, admin, users, bills, shippers, todos, managers, common

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
# app.include_router(admin.router)
app.include_router(bills.router)
app.include_router(shippers.router)
app.include_router(managers.router)
app.include_router(common.router)
app.include_router(todos.router)


app.mount("/static", StaticFiles(directory="static"), name="static")

# @app.exception_handler(HTTPException)
# async def redirect_404_handler(request: Request, exc: HTTPException):
#     if exc.status_code == 404:
#         return RedirectResponse(url="/common/page-404")
#     raise exc


@app.get("/")
def test(request: Request):
    return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)


templates = Jinja2Templates(directory="templates")

@app.get("/test_ui")
def test_ui(request: Request):
    return templates.TemplateResponse(name="base/base.html", context={"request": request})