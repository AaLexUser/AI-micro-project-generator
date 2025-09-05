import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Меняем только эту переменную, чтобы переключать БД:

DEFAULT_URL = "sqlite:///./app.db"


DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)

engine = create_engine(
    DATABASE_URL,
    echo=False,  # ставь True если хочешь видеть SQL
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass
