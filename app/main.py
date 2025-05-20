from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles
import os

from app.database import database, users  # Make sure this module is set up properly

app = FastAPI()

# Absolute paths for templates and static directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Jinja2 template configuration
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Connect to database on startup and disconnect on shutdown
@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()

@app.on_event("shutdown")
async def shutdown():
    if database.is_connected:
        await database.disconnect()

# Dependency to provide DB access
async def get_db():
    yield database

# Password utilities
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request, "username": "Guest"})

@app.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):
    query = users.select().where(users.c.username == username)
    existing_user = await db.fetch_one(query)
    if existing_user:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "User already exists"
        })

    hashed_password = hash_password(password)
    query = users.insert().values(username=username, password=hashed_password)
    await db.execute(query)
    return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):
    query = users.select().where(users.c.username == username)
    user = await db.fetch_one(query)
    if user and verify_password(password, user["password"]):
        return templates.TemplateResponse("welcome.html", {
            "request": request,
            "username": username
        })
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid username or password"
    })
