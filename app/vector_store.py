import os
from datetime import datetime

import cohere
import chromadb
from dotenv import load_dotenv

from app.document_processor import extract_pages_auto
from app.chunker import chunk_pages
from app.text_cleaner import clean_text

load_dotenv()

cohere_api_key = os.getenv("COHERE_API_KEY")

if not cohere_api_key:
    raise ValueError("Cohere API key not found!")

co = cohere.ClientV2(
    api_key=cohere_api_key
)

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_or_create_collection(
    name="documents"
)


def generate_embeddings(texts):
    """
    Generate Cohere embeddings in batches.
    """

    all_embeddings = []
    batch_size = 90

    for i in range(0, len(texts), batch_size):

        batch = texts[i:i + batch_size]

        print(
            f"Generating embeddings for chunks "
            f"{i + 1} to {i + len(batch)}..."
        )

        response = co.embed(
            model="embed-v4.0",
            input_type="search_document",
            texts=batch,
            embedding_types=["float"]
        )

        all_embeddings.extend(
            response.embeddings.float
        )

    return all_embeddings


def generate_query_embedding(query):
    """
    Generate an embedding for a user question.
    """

    response = co.embed(
        model="embed-v4.0",
        input_type="search_query",
        texts=[query],
        embedding_types=["float"]
    )

    return response.embeddings.float[0]


def document_exists(filename):
    """
    Check whether a document already exists.
    """

    results = collection.get(
        where={
            "source": filename
        },
        limit=1
    )

    return len(results["ids"]) > 0


def store_document_chunks(file_path, filename=None):
    """
    Extract, clean, chunk, embed and store a document.
    """

    if filename is None:
        filename = os.path.basename(file_path)

    if document_exists(filename):

        print(
            f"Document already exists: {filename}"
        )

        return {
            "status": "exists",
            "filename": filename,
            "chunks_added": 0
        }

    pages = extract_pages_auto(
        file_path
    )

    print(
        "Pages extracted:",
        len(pages)
    )

    cleaned_pages = []

    for page in pages:

        cleaned_text = clean_text(
            page["text"]
        )

        if cleaned_text:

            cleaned_pages.append({
                "text": cleaned_text,
                "page": page["page"]
            })

    print(
        "Pages with text:",
        len(cleaned_pages)
    )

    chunks = chunk_pages(
        cleaned_pages
    )

    print(
        "Total chunks created:",
        len(chunks)
    )

    if not chunks:
        raise ValueError(
            "No readable text found in the document."
        )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print(
        "Generating embeddings..."
    )

    embeddings = generate_embeddings(
        texts
    )

    safe_filename = filename.replace(
        " ",
        "_"
    )

    ids = [
        f"{safe_filename}_chunk_{i}"
        for i in range(len(chunks))
    ]

    uploaded_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    metadatas = []

    for chunk in chunks:

        metadatas.append({
            # IMPORTANT:
            # main.py uses "source" for document
            # library, delete and status checks.
            "source": filename,

            # Keep filename too for compatibility.
            "filename": filename,

            "page": chunk["page"],

            "file_type": os.path.splitext(
                filename
            )[1].lower(),

            "uploaded_at": uploaded_at
        })

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(
        "Chunks successfully stored in ChromaDB!"
    )

    print(
        "Total chunks in collection:",
        collection.count()
    )

    return {
        "status": "uploaded",
        "filename": filename,
        "pages": len(pages),
        "chunks": len(chunks)
    }


def search_similar(
    query,
    source="all",
    n_results=5
):
    """
    Search ChromaDB for relevant document chunks.
    """

    query_embedding = generate_query_embedding(
        query
    )

    if source and source != "all":

        results = collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=n_results,
            where={
                "source": source
            }
        )

    else:

        results = collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=n_results
        )

    return results


def delete_document(filename):
    """
    Delete all chunks belonging to a document.
    """

    results = collection.get(
        where={
            "source": filename
        }
    )

    document_ids = results["ids"]

    if document_ids:

        collection.delete(
            ids=document_ids
        )

    return {
        "status": "deleted",
        "filename": filename,
        "chunks_deleted": len(document_ids)
    }


def store_pdf_chunks(file_path, filename=None):
    """
    Backward-compatible PDF function.
    """

    return store_document_chunks(
        file_path,
        filename
    )