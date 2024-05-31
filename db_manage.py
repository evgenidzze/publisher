from sqlalchemy import String, ForeignKey, Text

from config import DB_PASS, DB_NAME, DB_HOST, DB_USER
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, DeclarativeMeta, declarative_base

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
engine = create_async_engine(url=DATABASE_URL)
async_session = async_sessionmaker(engine)
Base: DeclarativeMeta = declarative_base()
metadata = Base.metadata


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'User'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True)
    telegram_id: Mapped[str] = mapped_column(type_=String(45), nullable=True, unique=True)
    username: Mapped[str] = mapped_column(type_=String(45), nullable=True)
    is_admin: Mapped[bool] = mapped_column(nullable=False, default=False)

    def __repr__(self):
        return f'<User {self.telegram_id}>'


class Catalog(Base):
    __tablename__ = 'Catalog'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True)
    name: Mapped[str] = mapped_column(type_=String(255), nullable=False, unique=False)

    def __repr__(self):
        return f'<Catalog {self.name}>'


class Media(Base):
    __tablename__ = 'Media'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey('Catalog.id'), nullable=False)
    media_type: Mapped[str] = mapped_column(type_=String(45), nullable=False)
    file_id: Mapped[str] = mapped_column(type_=String(255), nullable=True)
    text: Mapped[str] = mapped_column(type_=Text(), nullable=True)

    def __repr__(self):
        return self.media_type


class Channel(Base):
    __tablename__ = 'Channel'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(type_=String(45), nullable=False)
    name: Mapped[str] = mapped_column(type_=String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(type_=String(45), nullable=False)
