from sqlmodel import (
    Field,
    Session,
    SQLModel,
    create_engine,
    select,
    JSON,
    Column,
    DateTime,
)
from sqlalchemy.sql import func
from typing import Annotated, Dict
from fastapi import Depends
from enum import Enum
from ulid import ULID
import bcrypt
from datetime import datetime


class UserTypeEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(SQLModel, table=True):
    id: str = Field(primary_key=True, default=lambda: str(ULID()))
    username: str = Field(index=True)
    password: str
    type: UserTypeEnum
    config: Dict = Field(default_factory=dict, sa_column=Column(JSON))

    class Config:
        arbitrary_types_allowed = True


class MessageTypeEnum(str, Enum):
    QUESTION = "question"
    ANSWER = "answer"


class Message(SQLModel, table=True):
    id: str = Field(primary_key=True, default=str(ULID()))
    chat_id: str = Field(index=True, default=str(ULID()))
    user_id: str = Field(index=True, nullable=True)
    type: MessageTypeEnum
    content: str
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )


sqlite_file_name = "database/data.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def add_initial_data():
    with Session(engine) as session:
        statement = select(User).where(User.username == "admin")
        result = session.exec(statement).first()
        if result:
            return  # already exists
        admin = User(
            id=str(ULID()),
            username="admin",
            password=bcrypt.hashpw(b"00000000", bcrypt.gensalt(14)).decode(),
            type="admin",
            attributes={},
        )
        session.add(admin)
        session.commit()


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
