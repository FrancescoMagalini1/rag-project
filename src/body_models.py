from pydantic import BaseModel
from enum import Enum


class TypeEnum(str, Enum):
    MARKDOWN = "markdown"
    TEXT = "text"


class DocumentBody(BaseModel):
    text: str
    type: TypeEnum
    dataset: str
