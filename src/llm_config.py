from langchain_mistralai import ChatMistralAI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_KEY: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

llm_model = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0,
    max_retries=2,
    api_key=settings.API_KEY,
)
