

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from core.settings import settings
from database.connection import engine, Base
from routes.auth_routes import router as auth_routes
from routes.user_router import router as user_routes
from routes.oauth_routes import router as oauth_routes

app = FastAPI(title = settings.app_name)

app.include_router(auth_routes)
app.include_router(user_routes)
app.include_router(oauth_routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:63342",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://rearmost-unvoluntarily-miss.ngrok-free.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware, #type: ignore
    secret_key=settings.secret_key,
)
app.add_middleware(
    CORSMiddleware, #type: ignore
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/")
def home():
    return {"message": "App is running"}

@app.get("/health")
def health():
    return {"status": "ok"}