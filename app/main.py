import os

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from app.rag_pipeline import ask_question

from app.vector_store import (
    store_document_chunks,
    collection
)


app = FastAPI(
    title="DocRAG API",
    description="AI-powered document question answering system",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# -----------------------------------
# REQUEST MODELS
# -----------------------------------

class ChatMessage(BaseModel):

    role: str

    content: str


class QuestionRequest(BaseModel):

    question: str

    source: str | None = None

    conversation_history: list[ChatMessage] = []


# -----------------------------------
# PROCESSING STATUS
# -----------------------------------

processing_status = {}


# -----------------------------------
# HOME
# -----------------------------------

@app.get("/")
def home():

    return {
        "message": "DocRAG API is running!"
    }


# -----------------------------------
# ASK QUESTION
# -----------------------------------

@app.post("/ask")
def ask(request: QuestionRequest):

    conversation_history = [
        message.model_dump()
        for message in request.conversation_history
    ]

    answer, sources = ask_question(
        request.question,
        source=request.source,
        conversation_history=conversation_history
    )

    return {
        "question": request.question,
        "answer": answer,
        "sources": sources
    }


# -----------------------------------
# BACKGROUND PROCESSING
# -----------------------------------

def process_document(
    file_path,
    filename
):

    processing_status[filename] = (
        "processing"
    )

    try:

        print(
            f"\nStarting background processing: "
            f"{file_path}"
        )

        result = store_document_chunks(
            file_path
        )

        processing_status[filename] = (
            "completed"
        )

        print(
            "\nBackground processing completed:"
        )

        print(result)

    except Exception as error:

        processing_status[filename] = (
            "failed"
        )

        print(
            "\nBackground processing failed:"
        )

        print(error)


# -----------------------------------
# UPLOAD DOCUMENT
# -----------------------------------

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):

    allowed_extensions = (
        ".pdf",
        ".docx"
    )

    filename = file.filename or ""

    if not filename.lower().endswith(
        allowed_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF and DOCX files "
                "are supported."
            )
        )

    os.makedirs(
        "uploads",
        exist_ok=True
    )

    file_path = os.path.join(
        "uploads",
        filename
    )

    contents = await file.read()

    with open(
        file_path,
        "wb"
    ) as f:

        f.write(contents)

    existing_documents = collection.get(
        where={
            "source": filename
        },
        limit=1
    )

    if existing_documents["ids"]:

        return {
            "message": (
                "This document is already uploaded."
            ),
            "filename": filename,
            "status": "exists"
        }

    processing_status[filename] = (
        "processing"
    )

    background_tasks.add_task(
        process_document,
        file_path,
        filename
    )

    return {
        "message": (
            "File uploaded successfully. "
            "Processing started in the background."
        ),
        "filename": filename,
        "status": "processing"
    }


# -----------------------------------
# GET DOCUMENTS
# -----------------------------------

@app.get("/documents")
def get_documents():

    results = collection.get(
        include=["metadatas"]
    )

    documents = {}

    for metadata in results["metadatas"]:

        source = metadata.get(
            "source"
        )

        if not source:
            continue

        if source not in documents:

            documents[source] = {

                "filename": source,

                "file_type": metadata.get(
                    "file_type",
                    "unknown"
                ),

                "pages": set(),

                "chunks": 0,

                "uploaded_at": metadata.get(
                    "uploaded_at",
                    "Unknown"
                )
            }

        page = metadata.get(
            "page"
        )

        if page is not None:

            documents[source]["pages"].add(
                page
            )

        documents[source]["chunks"] += 1

    document_list = []

    for document in documents.values():

        document["pages"] = len(
            document["pages"]
        )

        document_list.append(
            document
        )

    return {
        "documents": document_list
    }


# -----------------------------------
# DELETE DOCUMENT
# -----------------------------------

@app.delete(
    "/documents/{filename}"
)
def delete_document(
    filename: str
):

    results = collection.get(
        where={
            "source": filename
        }
    )

    document_ids = results["ids"]

    if not document_ids:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    collection.delete(
        ids=document_ids
    )

    file_path = os.path.join(
        "uploads",
        filename
    )

    if os.path.exists(file_path):

        os.remove(file_path)

    processing_status.pop(
        filename,
        None
    )

    return {

        "message": (
            "Document deleted successfully."
        ),

        "filename": filename,

        "chunks_deleted": len(
            document_ids
        )
    }


# -----------------------------------
# PROCESSING STATUS
# -----------------------------------

@app.get(
    "/documents/{filename}/status"
)
def get_processing_status(
    filename: str
):

    status = processing_status.get(
        filename
    )

    if status is None:

        if collection.get(
            where={
                "source": filename
            },
            limit=1
        )["ids"]:

            status = "completed"

        else:

            status = "unknown"

    return {

        "filename": filename,

        "status": status
    }