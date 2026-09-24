# DocRAG – LLM-Powered Document Q&A System

DocRAG is a full-stack Retrieval-Augmented Generation (RAG) application that allows users to upload documents and ask questions about their content.

The system processes PDF, DOCX, and scanned documents, extracts and cleans their text, creates semantic embeddings, retrieves relevant document chunks, and generates context-grounded responses using an LLM.

## 🚀 Live Demo

**Frontend:**  
https://docrag-frontend-9ncj.onrender.com

**Backend API:**  
https://docrag-api.onrender.com

---

## 📌 Project Overview

DocRAG is designed to make document-based information retrieval easier by allowing users to interact with their documents using natural language.

Instead of manually searching through lengthy documents, users can upload their files and ask questions. DocRAG retrieves the most relevant sections of the uploaded documents and uses them as context to generate grounded responses.

---

## ✨ Features

- Upload PDF and DOCX documents
- Process scanned documents using OCR
- Extract and clean document text
- Automatically divide documents into smaller chunks
- Generate semantic embeddings using Cohere
- Store embeddings using ChromaDB
- Perform semantic similarity search
- Ask natural-language questions about documents
- Retrieve information from multiple documents
- Conversation-aware question answering
- Document and page-level source citations
- Source relevance tracking
- Document library
- Duplicate document detection
- Delete uploaded documents
- Background document processing
- Processing status tracking
- React-based user interface
- FastAPI backend

---

## 🏗️ System Architecture

```text
                ┌──────────────────────┐
                │    React Frontend    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │     FastAPI API      │
                └──────────┬───────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
      Document Processing          Question Processing
              │                         │
              ▼                         ▼
       PDF / DOCX / OCR          Query Embedding
              │                         │
              ▼                         ▼
       Text Cleaning              ChromaDB Search
              │                         │
              ▼                         ▼
          Chunking              Relevant Chunks
              │                         │
              └────────────┬────────────┘
                           ▼
                  ┌─────────────────┐
                  │   Cohere LLM    │
                  └────────┬────────┘
                           │
                           ▼
                  Grounded Response
                    + Sources
## 🔄 How DocRAG Works

### 1. Document Upload

The user uploads a PDF or DOCX document through the React frontend.

### 2. Document Processing

The FastAPI backend receives the document and extracts its content.

- PDF files are processed using PyMuPDF
- DOCX files are processed using python-docx
- Scanned documents are processed using Tesseract OCR

### 3. Text Cleaning

The extracted text is cleaned and normalized before further processing.

### 4. Text Chunking

Large documents are divided into smaller chunks so that relevant sections can be retrieved efficiently.

### 5. Embedding Generation

Cohere embeddings are generated for the document chunks.

### 6. Vector Storage

The embeddings and document metadata are stored in ChromaDB.

### 7. Question Processing

When the user asks a question, the question is converted into an embedding.

### 8. Semantic Retrieval

ChromaDB searches for relevant document chunks based on semantic similarity.

### 9. Response Generation

The retrieved chunks are provided as context to the Cohere language model, which generates a response based on the available document content.

### 10. Source Citations

DocRAG returns relevant source information, including document and page-level references where available.

---

## 🛠️ Tech Stack

### Frontend

- React
- JavaScript
- HTML
- CSS

### Backend

- Python
- FastAPI

### AI / RAG

- Cohere
- ChromaDB
- Retrieval-Augmented Generation (RAG)

### Document Processing

- PyMuPDF
- python-docx
- Tesseract OCR

### Development Tools

- Git
- GitHub
- VS Code

### Deployment

- Render

---

## 📂 Project Structure

```text
DocRAG/
│
├── app/
│   ├── main.py
│   ├── document_processor.py
│   └── ...
│
├── frontend/
│   └── ...
│
├── uploads/
│
├── requirements.txt
├── .gitignore
├── README.md
└── ...
```

---

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/tyagikanishka8-debug/DocRAG.git
cd DocRAG
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root and add your Cohere API key:

```text
COHERE_API_KEY=your_cohere_api_key
```

Do not commit your API key or `.env` file to GitHub.

### 6. Start the Backend

```bash
uvicorn app.main:app --reload
```

The backend will run locally at:

```text
http://127.0.0.1:8000
```

### 7. Start the Frontend

Open a new terminal and navigate to the frontend directory.

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

---

## 🔐 Environment Variables

DocRAG requires API credentials for the Cohere API.

Example:

```text
COHERE_API_KEY=your_api_key
```

API keys should never be uploaded to GitHub.

The `.env` file should be excluded using `.gitignore`.

---

## 📚 Key Concepts Demonstrated

This project demonstrates practical implementation of:

- Retrieval-Augmented Generation
- Large Language Models
- Semantic Search
- Vector Databases
- Text Embeddings
- Natural Language Processing
- Optical Character Recognition
- REST APIs
- Full-Stack Development
- Document Processing
- Asynchronous Processing
- Metadata Management

---

## 🎯 Learning Outcomes

Through this project, the following concepts were implemented and explored:

- Building an end-to-end RAG pipeline
- Working with LLM APIs
- Generating and storing embeddings
- Implementing semantic retrieval
- Processing different document formats
- Integrating OCR into a document pipeline
- Building APIs using FastAPI
- Developing a React frontend
- Connecting frontend and backend systems
- Managing source citations and metadata
- Using Git and GitHub for version control
- Deploying a full-stack application

---

## 👩‍💻 Author

**Kanishka Tyagi**

B.Tech – Computer Science and Engineering

JECRC University

**GitHub:**

https://github.com/tyagikanishka8-debug

**LinkedIn:**

https://www.linkedin.com/in/kanishkatyagi14

---

## 📄 Project Status

**Status:** Completed

DocRAG was developed as a full-stack academic project demonstrating the practical implementation of Retrieval-Augmented Generation, document processing, semantic search, and LLM-based question answering.