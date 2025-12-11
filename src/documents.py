from docling.document_converter import DocumentConverter
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from src.body_models import DocumentBody
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# example "https://arxiv.org/pdf/2408.09869"


def parse_document(file: str):
    converter = DocumentConverter()
    doc = converter.convert(file).document
    return doc.export_to_markdown()


def split_document(doc: DocumentBody):
    chunks: list[str] = []
    if doc.type == "text":
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )
        chunks = text_splitter.split_text(doc.text)
    else:
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on, strip_headers=False
        )
        chunks = markdown_splitter.split_text(doc.text)
    return chunks


def save_embeddings(chunks: list[str]):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
