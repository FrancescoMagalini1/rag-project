from fastapi import FastAPI, Request, Form, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.models import create_db_and_tables, add_initial_data, SessionDep
from src.body_models import DocumentBody
from contextlib import asynccontextmanager
from typing import Annotated
from src.utils import (
    perform_login,
    authenticate,
    create_new_message,
    get_latest_chats,
    get_chat_messages,
    get_previous_questions,
)
from fastapi.responses import RedirectResponse
from src.documents import (
    split_document,
    save_embeddings,
    retrieve_context,
    get_stats,
    llm_summary,
    retrieve_all_documents,
)
from src.llm import llm_answer, agent_answer
from ulid import ULID
from fastapi.responses import HTMLResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    add_initial_data()
    yield


description = """
A compact web server implementing all the essentials for creating a Retrieval Augmented Generation pipeline.
"""

app = FastAPI(lifespan=lifespan, title="RAG Project", description=description)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/api/hello")
async def hello():
    """
    A simple endpoint for checking the availability of the server
    """
    return {"message": "Hello World"}


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    sql_session: SessionDep,
    rag_jwt_token: Annotated[str | None, Cookie()] = None,
):
    """
    Returns the Home page on a new chat. Available for both authenticated and unauthenticated users.
    """
    user = None
    if rag_jwt_token:
        user = authenticate(rag_jwt_token, sql_session)
    return templates.TemplateResponse(
        request=request,
        name="home.jinja",
        context={"user": user, "page": "home", "chat_id": str(ULID()), "messages": []},
    )


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """
    Returns the login page.
    """
    return templates.TemplateResponse(
        request=request, name="login.jinja", context={"error": None}
    )


@app.post("/login", response_class=HTMLResponse)
async def login_request(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    sql_session: SessionDep,
):
    """This endpoint handles the login request.
    If successfull it will initiate the authentication session by instantiating a JWT as  a cookie.
    """
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


@app.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    sql_session: SessionDep,
    rag_jwt_token: Annotated[str | None, Cookie()] = None,
):
    user = None
    if rag_jwt_token:
        user = authenticate(rag_jwt_token, sql_session)
    if user:
        return templates.TemplateResponse(
            request=request,
            name="profile.jinja",
            context={"user": user, "page": "profile"},
        )
    else:
        return RedirectResponse("/login", status_code=302)


@app.get("/chats", response_class=HTMLResponse)
async def chats(
    request: Request,
    sql_session: SessionDep,
    rag_jwt_token: Annotated[str | None, Cookie()] = None,
):
    """Returns the Chats page. A list of the _n_ (=50) most recent chats from newest to oldest."""
    user = None
    if rag_jwt_token:
        user = authenticate(rag_jwt_token, sql_session)
    if user:
        chats = get_latest_chats(user, sql_session)
        return templates.TemplateResponse(
            request=request,
            name="chats.jinja",
            context={"user": user, "page": "chats", "chats": chats},
        )
    else:
        return RedirectResponse("/login", status_code=302)
    # return templates.TemplateResponse(request=request, name="profile.jinja")


@app.get("/chats/{chat_id}", response_class=HTMLResponse)
async def chat(
    chat_id: str,
    request: Request,
    sql_session: SessionDep,
    rag_jwt_token: Annotated[str | None, Cookie()] = None,
):
    """Returns a specific chat page. The LLM is able to understand a certain degree of
    context based on the previous questions asked."""
    user = None
    if rag_jwt_token:
        user = authenticate(rag_jwt_token, sql_session)
    if user:
        messages = get_chat_messages(chat_id, user, sql_session)
        return templates.TemplateResponse(
            request=request,
            name="home.jinja",
            context={
                "user": user,
                "page": "chats",
                "chat_id": chat_id,
                "messages": messages,
            },
        )
    else:
        return RedirectResponse("/login", status_code=302)


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
    """
    Add a new document to the internal database. Either a simple text or a structured one with markdown syntax.

    **title** Title or Filename \n
    **text** Text content \n
    **type** "markdown" or "text" \n
    **dataset** Name of the dataset or category, to which this document belongs \n
    **summary** Short summary (optional)
    """
    chunks = split_document(body)
    save_embeddings(chunks)
    return {"message": "OK"}


@app.get("/api/documents")
async def get_documents():
    """
    Retrieve all the chunks saved in the internal database
    """
    docs = retrieve_all_documents()
    return {"docs": docs}


@app.post("/api/summarize")
async def summarize(body: DocumentBody):
    """
    Create a short summary for a document

    **title** Title or Filename \n
    **text** Text content \n
    **type** "markdown" or "text" \n
    **dataset** Name of the dataset or category, to which this document belongs \n
    **summary** Short summary (optional)
    """
    summary = llm_summary(body)
    return {"message": summary}


@app.get("/api/documents/stats")
async def get_documents_stats():
    """Get the number of documents saved in the internal database"""
    num_docs = get_stats()
    return {"number of documents": num_docs}


@app.get("/api/retrieve")
async def retrieve(query: str = ""):
    """Get the top _n_ (=5) most relevant documents given a user query"""
    output = ""
    if query:
        output = retrieve_context(query)
    return {"context": output[0]}


@app.get("/api/answer")
async def provide_answer(
    sql_session: SessionDep,
    rag_jwt_token: Annotated[str | None, Cookie()] = None,
    message: str = "",
    chat_id: str = "",
):
    """Get the LLM answer given a user query. The LLM will get the top _n_ (=5) most relevant documents given the user query,
    plus a brief context by using eventual previous questions (if the user is authenticated)
    """
    output = "answer"
    if message:
        user = None
        if rag_jwt_token:
            user = authenticate(rag_jwt_token, sql_session)
        messages = None
        if user and len(chat_id):
            messages = get_previous_questions(chat_id, user, sql_session)
        output = agent_answer(message, messages)
        if user and len(chat_id):
            question_id = str(ULID())
            answer_id = str(ULID())
            create_new_message(
                question_id, message, user, chat_id, "question", sql_session
            )
            create_new_message(answer_id, output, user, chat_id, "answer", sql_session)

    return output
