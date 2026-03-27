
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from core.settings import settings
from routes.auth_routes import router as auth_routes
from routes.oauth_routes import router as oauth_routes
from routes.user_router import router as user_routes

app = FastAPI(title=settings.app_name)

app.include_router(auth_routes)
app.include_router(user_routes)
app.include_router(oauth_routes)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,  # type: ignore
    secret_key=settings.secret_key,
)

@app.get("/")
def home():
    return {"message": "App is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
