from src.documents import retrieve_context_tool
from langchain.agents import create_agent
from datetime import datetime
from langchain_core.load import dumps
from src.models import Message
from src.llm_config import llm_model


tools = [retrieve_context_tool]
prompt = (
    "You have access to a tool that retrieves possible context sections."
    """Use the tool to help answer user queries. You are free pick only the sections that you think are useful. 
    Please do not reply using markdown but just text."""
)
agent = create_agent(llm_model, tools, system_prompt=prompt)


def llm_answer(query: str):
    return llm_model.invoke(query)


def provide_conversation_context(messages: list[Message]):
    # This function takes a list of Message objects representing a conversation and generates a summary of the conversation's
    # context using a language model.
    query = (
        "\n".join([m.content for m in messages])
        + "Above there are some questions asked by a user. Shortly summarize the context of the conversation for a future prompt by completing the phrase: The topic of the conversation is ..."
    )
    return llm_model.invoke(query).content


def agent_answer(query: str, messages: list[Message] | None):
    # This function takes a user query and an optional list of Message objects representing a conversation.
    # It generates a response to the query using an agent that has access to the conversation context and
    # tools for retrieving relevant information.
    chat_context = ""
    if messages and len(messages):
        chat_context = provide_conversation_context(messages)
    if len(chat_context):
        query = "(" + chat_context + "). " + query
    response = agent.invoke({"messages": [{"role": "user", "content": query}]})
    print(response)
    now = datetime.now()
    # log the chain
    with open(
        f'logs/{now.astimezone().strftime("%Y-%m-%d %H-%M-%S")} logs.json', "w"
    ) as f:
        json_str = dumps(response, pretty=True)
        f.write(json_str)

    return response["messages"][-1].content
