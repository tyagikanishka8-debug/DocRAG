
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.document_processor import process_document
from app.rag_pipeline import ask_question
from app.vector_store import (
    collection,
    delete_document as remove_document_from_store,
    document_exists,
    store_document_chunks,
)

load_dotenv()

app = FastAPI(title="DocRAG API")

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class QuestionRequest(BaseModel):
    question: str
    source: str = "all"
    conversation_history: list = []


def process_uploaded_document(file_path: str, filename: str):
    """
    Background document processing.

    Extracts the document, creates chunks, generates embeddings,
    and stores everything in ChromaDB.
    """
    try:
        print(f"Starting background processing: {file_path}")

        result = process_document(file_path)

        if isinstance(result, dict):
            status = result.get("status")
            pages = result.get("pages", 0)
            chunks = result.get("chunks", 0)

            if status == "error":
                print(f"Background processing failed: {result}")
                return result

        else:
            pages = 0
            chunks = 0

        store_result = store_document_chunks(
            file_path,
            filename=filename,
        )

        print(
            "Background processing completed:",
            {
                "status": "success",
                "filename": filename,
                "pages": pages,
                "chunks": chunks,
            },
        )

        return {
            "status": "success",
            "filename": filename,
            "pages": pages,
            "chunks": chunks,
            "store_result": store_result,
        }

    except Exception as exc:
        print(
            f"Background processing failed for {filename}: {exc}"
        )

        return {
            "status": "failed",
            "filename": filename,
            "error": str(exc),
        }


@app.get("/")
def root():
    return {
        "message": "DocRAG API is running",
        "status": "healthy",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    filename = file.filename

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(filename).suffix.lower()

    if extension not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    if document_exists(filename):
        raise HTTPException(
            status_code=400,
            detail=f"{filename} already exists in the document library.",
        )

    file_path = UPLOAD_DIR / filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {exc}",
        )

    background_tasks.add_task(
        process_uploaded_document,
        str(file_path),
        filename,
    )

    return {
        "status": "processing",
        "filename": filename,
        "message": "Document uploaded successfully and processing has started.",
    }


@app.get("/documents")
def get_documents():
    try:
        results = collection.get(include=["metadatas"])

        documents = {}

        metadatas = results.get("metadatas", []) or []

        for metadata in metadatas:
            if not metadata:
                continue

            source = metadata.get("source") or metadata.get("filename")

            if not source:
                continue

            if source not in documents:
                documents[source] = {
                    "filename": source,
                    "file_type": metadata.get(
                        "file_type",
                        Path(source).suffix,
                    ),
                    "pages": set(),
                    "chunks": 0,
                    "uploaded_at": metadata.get(
                        "uploaded_at",
                        "",
                    ),
                }

            page = metadata.get("page")

            if page is not None:
                documents[source]["pages"].add(page)

            documents[source]["chunks"] += 1

        formatted_documents = []

        for document in documents.values():
            document["pages"] = len(document["pages"])

            formatted_documents.append(document)

        formatted_documents.sort(
            key=lambda item: item.get("uploaded_at", ""),
            reverse=True,
        )

        return {
            "documents": formatted_documents,
        }

    except Exception as exc:
        print(f"Failed to load documents: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to load documents.",
        )


@app.get("/documents/{filename}/status")
def document_status(filename: str):
    try:
        results = collection.get(
            where={"source": filename},
            include=["metadatas"],
        )

        metadatas = results.get("metadatas", []) or []

        if metadatas:
            return {
                "status": "completed",
                "filename": filename,
            }

        upload_path = UPLOAD_DIR / filename

        if upload_path.exists():
            return {
                "status": "processing",
                "filename": filename,
            }

        return {
            "status": "not_found",
            "filename": filename,
        }

    except Exception as exc:
        print(
            f"Failed to check status for {filename}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Could not check document status.",
        )


@app.delete("/documents/{filename}")
def delete_document(filename: str):
    try:
        removed = remove_document_from_store(filename)

        file_path = UPLOAD_DIR / filename

        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as exc:
                print(
                    f"Could not remove uploaded file: {exc}"
                )

        if not removed:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        return {
            "status": "success",
            "filename": filename,
            "message": "Document deleted successfully.",
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"Failed to delete document {filename}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete document.",
        )


@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        result = ask_question(
            question=question,
            source=request.source,
            conversation_history=request.conversation_history,
        )

        # rag_pipeline.ask_question returns a dictionary.
        # Do NOT unpack it as:
        # answer, sources = result
        #
        # because that would return the dictionary keys
        # ("answer", "sources") instead of their values.

        if isinstance(result, dict):
            answer = result.get("answer", "")
            sources = result.get("sources", [])

        else:
            # Compatibility fallback in case the pipeline
            # returns a tuple.
            answer, sources = result

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    except Exception as exc:
        print(f"Question processing failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {exc}",
        )

