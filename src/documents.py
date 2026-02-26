from docling.document_converter import DocumentConverter
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from src.body_models import DocumentBody
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document
from langchain_community.tools import tool
import os
from langchain_classic.retrievers.contextual_compression import (
    ContextualCompressionRetriever,
)
from langchain_community.document_compressors import FlashrankRerank
from src.llm_config import llm_model
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

# example "https://arxiv.org/pdf/2408.09869"


def parse_document(file: str):
    converter = DocumentConverter()
    doc = converter.convert(file).document
    return doc.export_to_markdown()


def llm_summary(doc: DocumentBody):
    # This function generates a short but descriptive title for a document using a language model.
    prompt = f"""Generate a very short but highly descriptive title (not in markdown format, just a simple text) that describes a file given the filename: {doc.title} 
    , and the text: {doc.text}. """
    return llm_model.invoke(prompt).content


def split_document(doc: DocumentBody):
    # This function takes a DocumentBody object and splits its text into smaller chunks based on the document type
    # (text or markdown).
    chunks: list[Document] = []
    if doc.type == "text":
        summary = doc.summary
        if not summary:
            summary = llm_summary(doc)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )
        raw_chunks = text_splitter.split_text(doc.text)
        for i, chunk in enumerate(raw_chunks):
            page_content = f"Title: {summary}\nContent: {chunk}"
            chunks.append(
                Document(
                    page_content=page_content,
                    metadata={
                        "source": doc.title,
                        "chunk": i,
                        "type": "text",
                        "dataset": doc.dataset,
                        "summary": summary,
                    },
                )
            )
    else:
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on, strip_headers=False
        )
        raw_chunks = markdown_splitter.split_text(doc.text)
        for i, chunk in enumerate(raw_chunks):
            chunks.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": doc.title,
                        "chunk": i,
                        "type": "markdown",
                        "dataset": doc.dataset,
                    },
                )
            )
    return chunks


INDEX_DIR = "database"
INDEX_NAME = "vector_index"
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
faiss_file = os.path.join(INDEX_DIR, f"{INDEX_NAME}.faiss")
pkl_file = os.path.join(INDEX_DIR, f"{INDEX_NAME}.pkl")
compressor = FlashrankRerank(top_n=5)


def get_vector_store():
    # This function checks if the FAISS index files exist. If they do, it loads the existing vector store.
    # If not, it creates a new vector store with a dummy document (which is immediately deleted) and saves it to disk.
    if os.path.exists(faiss_file) and os.path.exists(pkl_file):
        vector_store = FAISS.load_local(
            INDEX_DIR, embeddings, INDEX_NAME, allow_dangerous_deserialization=True
        )
    else:
        vector_store = FAISS.from_texts(
            texts=["dummy"], embedding=embeddings  # or initial documents
        )
        vector_store.delete([vector_store.index_to_docstore_id[0]])
        vector_store.save_local(INDEX_DIR, INDEX_NAME)
    return vector_store


def get_ensemble_retriever():
    # This function creates an ensemble retriever that combines a BM25 retriever and a vector store retriever.
    vector_store = get_vector_store()
    docs = []
    for doc_id in vector_store.index_to_docstore_id.values():
        doc = vector_store.docstore.search(doc_id)
        docs.append(doc)
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 15
    vector_store = vector_store.as_retriever(search_kwargs={"k": 15, "fetch_k": 50})
    return EnsembleRetriever(
        retrievers=[bm25_retriever, vector_store], weights=[0.6, 0.4]
    )


def save_embeddings(chunks: list[Document]):
    # This function takes a list of Document objects (chunks) and saves their embeddings to the vector store.
    vector_store = get_vector_store()
    vector_store.add_documents(documents=chunks)
    vector_store.save_local(INDEX_DIR, INDEX_NAME)


def get_stats():
    # This is a helper function to get statistics about the number of documents in the vector store,
    # which can be useful for monitoring and debugging.
    vector_store = get_vector_store()
    num_docs = vector_store.index.ntotal
    return num_docs


def retrieve_all_documents():
    # This is a helper function to retrieve all documents from the vector store, which can be useful for debugging or analysis.
    vector_store = get_vector_store()
    docs = []
    for doc_id in vector_store.index_to_docstore_id.values():
        doc = vector_store.docstore.search(doc_id)
        docs.append(doc)
    return docs


def retrieve_context(query: str):
    # This function retrieves relevant documents based on a query using a contextual compression retriever that combines
    # the ensemble retriever with a FlashrankRerank compressor.
    ensemble_retriever = get_ensemble_retriever()
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=ensemble_retriever
    )
    retrieved_docs = compression_retriever.invoke(query)
    serialized = "\n\n".join((f"{doc.page_content}") for doc in retrieved_docs)
    return serialized, retrieved_docs


@tool(response_format="content_and_artifact")
def retrieve_context_tool(query: str):
    """Retrieve information to help answer a query."""
    return retrieve_context(query)
