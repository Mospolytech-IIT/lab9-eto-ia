"""
Приложение FastAPI для управления пользователями и постами.
"""

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from starlette.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

# Подключение к базе данных PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:Memento227@192.168.56.1:5432/postgres"

# Создание экземпляра базы данных
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    """
    Модель для таблицы 'users'.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    """
    Модель для таблицы 'posts'.
    """
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")

# Создание таблиц
Base.metadata.create_all(engine)

# Сессия для работы с базой данных
Session = sessionmaker(bind=engine)
session = Session()

# Создание FastAPI приложения
app = FastAPI()

# Шаблоны для HTML страниц
templates = Jinja2Templates(directory="templates")

class UserCreate(BaseModel):
    """
    Модель для создания пользователя через API.
    """
    username: str
    email: EmailStr
    password: str

class PostCreate(BaseModel):
    """
    Модель для создания поста через API.
    """
    id: int | None = None  # ID поста необязателен
    title: str
    content: str
    user_id: int

class EmailUpdate(BaseModel):
    """
    Модель для обновления email пользователя.
    """
    new_email: EmailStr

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    """
    Возвращает главную страницу приложения с отображением всех пользователей и постов.
    """
    users = session.query(User).all()
    posts = session.query(Post).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "users": users, "posts": posts}
    )

@app.post("/users/")
async def create_user(user: UserCreate):
    """
    Создает нового пользователя.
    """
    existing_user = session.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Такой пользователь уже есть")
    new_user = User(username=user.username, email=user.email, password=user.password)
    session.add(new_user)
    session.commit()
    print(f"Added user: {new_user}")  # Логгирование добавленного пользователя
    return {"message": "User added successfully"}


@app.post("/posts/")
async def create_post(post: PostCreate):
    """
    Создает новый пост.
    """
    user = session.query(User).filter(User.id == post.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Проверка, если ID поста уже существует
    if post.id:
        existing_post = session.query(Post).filter(Post.id == post.id).first()
        if existing_post:
            raise HTTPException(status_code=400, detail="Post with this ID already exists.")

    # Создание нового поста
    new_post = Post(
        id=post.id,  # Если передан, используется этот ID, иначе генерируется автоматически
        title=post.title,
        content=post.content,
        user_id=post.user_id
    )
    session.add(new_post)
    session.commit()
    return {"message": "Post added successfully"}


# Обновление email
@app.put("/users/{user_id}/email/")
async def update_user_email(user_id: int, email_update: EmailUpdate):
    """
    Обновляет email пользователя.
    """
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.email = email_update.new_email
    session.commit()
    return {"message": "Email updated successfully"}

@app.get("/users/")
async def get_users(request: Request):
    """
    Возвращает список всех пользователей.
    """
    users = session.query(User).all()
    print(f"Retrieved users: {users}")  # Логгирование пользователей для проверки
    return templates.TemplateResponse(
        "all_users.html",
        {"request": request, "users": users}
    )

@app.get("/posts/")
async def get_posts(request: Request):
    """
    Возвращает список всех постов.
    """
    posts = session.query(Post).all()
    print(f"Retrieved posts: {posts}")  # Логгирование постов для проверки
    return templates.TemplateResponse(
        "all_posts.html",
        {"request": request, "posts": posts}
    )

@app.delete("/posts/{post_id}/")
async def delete_post(post_id: int):
    """
    Удаляет пост по ID.
    """
    post = session.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    session.delete(post)
    session.commit()
    return {"message": "Post deleted successfully"}

@app.delete("/users/{user_id}/")
async def delete_user_and_posts(user_id: int):
    """
    Удаляет пользователя и все связанные с ним посты.
    """
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Удаление всех постов пользователя
    session.query(Post).filter(Post.user_id == user_id).delete()

    # Удаление пользователя
    session.delete(user)
    session.commit()

    return {"message": "User and all associated posts deleted successfully"}

@app.post("/posts/{post_id}/edit")
async def edit_post(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    user_id: int = Form(...),
):
    """
    Редактирует пост.
    """
    post = session.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    post.title = title
    post.content = content
    post.user_id = user_id
    session.commit()
    return {"message": "Post updated successfully"}
