import bcrypt
from src.models import SessionDep, User
from sqlmodel import select
import jwt


def perform_login(username: str, password: str, sql_session: SessionDep):
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
    payload = jwt.decode(jwt_token, "secret", algorithms="HS256")
    if "id" in payload:
        statement = select(User).where(User.id == payload["id"])
        result = sql_session.exec(statement).first()
        return result
    return None
