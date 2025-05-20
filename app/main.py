from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

from app.database import database, users

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup", response_class=HTMLResponse)
async def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    query = users.select().where(users.c.username == username)
    existing_user = await database.fetch_one(query)
    if existing_user:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "User already exists"})
    
    query = users.insert().values(username=username, password=password)
    await database.execute(query)
    return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    query = users.select().where(users.c.username == username)
    user = await database.fetch_one(query)
    if user and user["password"] == password:
        return templates.TemplateResponse("welcome.html", {"request": request, "username": username})
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})
