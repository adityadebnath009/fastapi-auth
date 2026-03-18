import os

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from database.connection import engine, Base
from routes.auth_routes import router as auth_routes
from routes.user_router import router as user_routes
from routes.oauth_routes import router as oauth_routes

app = FastAPI()

app.include_router(auth_routes)
app.include_router(user_routes)
app.include_router(oauth_routes)

Base.metadata.create_all(bind=engine)
app.add_middleware(
    SessionMiddleware, #type: ignore
    secret_key=os.getenv("SECRET_KEY"),
)
app.add_middleware(
    CORSMiddleware, #type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"Hello"," World"}

