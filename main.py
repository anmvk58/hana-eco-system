from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

import models
from database import engine
from routers import auth, admin, users, bills, shippers, todos

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(bills.router)
app.include_router(shippers.router)
app.include_router(todos.router)


app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def test(request: Request):
    return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)

