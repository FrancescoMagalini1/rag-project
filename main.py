from fastapi import FastAPI, Request, Form, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.models import create_db_and_tables, add_initial_data, SessionDep
from src.body_models import DocumentBody
from contextlib import asynccontextmanager
from typing import Annotated
from src.utils import perform_login, authenticate
from fastapi.responses import RedirectResponse
from src.documents import split_document


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    add_initial_data()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/api/hello")
async def hello():
    return {"message": "Hello World"}


@app.get("/")
async def home(
    request: Request,
    sql_session: SessionDep,
    rag_jwt_token: Annotated[str | None, Cookie()] = None,
):
    user = None
    if rag_jwt_token:
        user = authenticate(rag_jwt_token, sql_session)
    return templates.TemplateResponse(
        request=request, name="home.jinja", context={"user": user}
    )


@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.jinja", context={"error": None}
    )


@app.post("/login")
async def login_request(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    sql_session: SessionDep,
):
    jwt = perform_login(username, password, sql_session)
    if jwt:
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("rag_jwt_token", jwt)
        return response
    else:
        return templates.TemplateResponse(
            request=request,
            name="login.jinja",
            context={"error": "Username o password errati"},
        )


"""
@app.post("/api/documents/process")
async def process_document(file: str | None = None):
    result = "no document URL provided"
    if file:
        result = parse_document(file)
    return {result}
"""


@app.post("/api/documents")
async def add_document(body: DocumentBody):
    chunks = split_document(body)

    return {"message": chunks}
