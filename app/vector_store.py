import os
import chromadb
import cohere
from dotenv import load_dotenv

from app.document_processor import extract_pages_auto
from app.chunker import chunk_pages

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="documents"
)


def embed_texts(texts):
    response = co.embed(
        model="embed-v4.0",
        texts=texts,
        input_type="search_document",
        embedding_types=["float"]
    )

    return response.embeddings.float


def embed_query(query):
    response = co.embed(
        model="embed-v4.0",
        texts=[query],
        input_type="search_query",
        embedding_types=["float"]
    )

    return response.embeddings.float[0]


def document_exists(filename):
    results = collection.get(
        where={"filename": filename}
    )

    return len(results.get("ids", [])) > 0


def store_document_chunks(file_path, filename=None):
    """
    Extract, chunk, embed and store a document.

    filename is optional so both the old and new
    calling styles remain compatible.
    """

    if filename is None:
        filename = os.path.basename(file_path)

    if document_exists(filename):
        return {
            "status": "duplicate",
            "filename": filename
        }

    pages = extract_pages_auto(file_path)

    chunks = chunk_pages(pages)

    if not chunks:
        return {
            "status": "error",
            "message": "No readable text found in the document."
        }

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embed_texts(texts)

    ids = []
    metadatas = []

    for index, chunk in enumerate(chunks):

        ids.append(
            f"{filename}_{index}"
        )

        metadatas.append({
            "filename": filename,
            "page": chunk.get("page", 0),
            "file_type": os.path.splitext(filename)[1].lower()
        })

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return {
        "status": "success",
        "filename": filename,
        "pages": len(pages),
        "chunks": len(chunks)
    }


def store_pdf_chunks(file_path, filename=None):
    return store_document_chunks(
        file_path,
        filename
    )


def search_similar(
    query,
    source="all",
    n_results=5
):
    query_embedding = embed_query(query)

    if source and source != "all":
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"filename": source}
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

    return results


def delete_document(filename):
    results = collection.get(
        where={"filename": filename}
    )

    ids = results.get("ids", [])

    if ids:
        collection.delete(ids=ids)

    return {
        "status": "deleted",
        "filename": filename,
        "deleted_chunks": len(ids)
    }