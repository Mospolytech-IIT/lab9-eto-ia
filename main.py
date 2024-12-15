"""
Основной модуль для настройки базы данных и определения моделей.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Подключение к базе данных PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:Memento227@192.168.56.1:5432/postgres"

# Создание экземпляра базы данных
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    """
    Модель таблицы 'users' в базе данных.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    """
    Модель таблицы 'posts' в базе данных.
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
