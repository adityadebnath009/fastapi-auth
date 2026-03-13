from fastapi import FastAPI

from database.connection import engine, Base
from routes.auth_routes import router as auth_routes
from routes.user_router import router as user_routes
app = FastAPI()

app.include_router(auth_routes)
app.include_router(user_routes)
Base.metadata.create_all(bind=engine) #the server starts creating tables automatically

posts: list[dict] = [
    {
        "id": 1,
        "author": "Corey Schafer",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Jane Doe",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "April 21, 2025",
    },
]

@app.get("/")
def home():
    return {"Hello"," World"}

@app.get("/api/posts")
def get_posts():
    return posts