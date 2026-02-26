import bcrypt
from src.models import SessionDep, User, Message, MessageTypeEnum
from sqlmodel import select
import jwt
from sqlalchemy.sql import func, and_


def perform_login(username: str, password: str, sql_session: SessionDep):
    # This is used to perform the login of a user.
    # It checks if the username exists in the database and if the password is correct.
    statement = select(User).where(User.username == username)
    result = sql_session.exec(statement).first()
    if result:
        check = bcrypt.checkpw(password.encode(), result.password.encode())
        if check:
            encoded_jwt = jwt.encode({"id": result.id}, "secret", algorithm="HS256")
            return encoded_jwt
        else:
            return None
    else:
        return None


def authenticate(jwt_token: str, sql_session: SessionDep):
    # This is used to authenticate a user based on the JWT token stored in the cookie.
    # It decodes the token to retrieve the user ID and then queries the database to get the user object.
    payload = jwt.decode(jwt_token, "secret", algorithms="HS256")
    if "id" in payload:
        statement = select(User).where(User.id == payload["id"])
        result = sql_session.exec(statement).first()
        return result
    return None


def create_new_message(
    id: str,
    content: str,
    user: User,
    chat_id: str,
    type: MessageTypeEnum,
    sql_session: SessionDep,
):
    # This is used to create a new message in the database.
    # It takes the content of the message, the user who sent it, the chat it belongs to, and its type (question or answer).
    new_message = Message(
        id=id, user_id=user.id, type=type, content=content, chat_id=chat_id
    )
    sql_session.add(new_message)
    sql_session.commit()


def get_latest_chats(user: User, sql_session: SessionDep):
    # This is used to retrieve the latest chats of a user.
    # It retrieves the most recent message of each chat and then orders them by creation time.
    subquery = (
        select(Message.chat_id, func.min(Message.id).label("first"))
        .where(Message.user_id == user.id)
        .group_by(Message.chat_id)
        .subquery()
    )

    query = (
        select(Message)
        .join(
            subquery,
            and_(
                Message.chat_id == subquery.c.chat_id,
                Message.id == subquery.c.first,
            ),
        )
        .where(Message.user_id == user.id)
        .order_by(-Message.id)
        .limit(50)
    )
    result = sql_session.exec(query)
    return [msg.model_dump() for msg in result.all()]


def get_chat_messages(chat_id: str, user: User, sql_session: SessionDep):
    # This is used to retrieve all the messages of a specific chat, ordered by their creation time.
    query = (
        select(Message)
        .where(and_(Message.chat_id == chat_id, Message.user_id == user.id))
        .order_by(Message.id)
    )
    result = sql_session.exec(query)
    return result.all()


def get_previous_questions(chat_id: str, user: User, sql_session: SessionDep):
    # This is used to provide context to the LLM.
    # It can be used to retrieve the previous questions asked by the user in a specific chat.
    query = (
        select(Message)
        .where(
            and_(
                Message.chat_id == chat_id,
                Message.user_id == user.id,
                Message.type == "question",
            )
        )
        .order_by(Message.id)
    )
    result = sql_session.exec(query)
    return result.all()
