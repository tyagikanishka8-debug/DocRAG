# DocRAG — AI Document Q&A System

DocRAG is an AI-powered document question-answering system that allows users to upload documents and ask natural-language questions about their content.

It uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from uploaded documents before generating grounded answers.

## ✨ Features

- Upload PDF and DOCX documents
- Automatic PDF text extraction
- OCR support for scanned PDFs
- Text cleaning and intelligent chunking
- Semantic search using embeddings
- Persistent vector storage with ChromaDB
- AI-powered answers using Cohere
- Multi-document support
- Document-specific question answering
- Source citations with page numbers
- Retrieved text snippets
- Relevance scores
- Confidence indicators
- Conversation-aware follow-up questions
- Background document processing
- Document library with metadata
- Delete uploaded documents
- React-based frontend
- FastAPI backend

## 🏗️ Architecture

```text
React Frontend
       ↓
    FastAPI
       ↓
 Document Upload
       ↓
 PDF / DOCX / OCR
       ↓
 Text Cleaning
       ↓
 Intelligent Chunking
       ↓
 Cohere Embeddings
       ↓
    ChromaDB
       ↓
 Semantic Retrieval
       ↓
 Relevant Document Chunks
       ↓
 Cohere LLM
       ↓
 Grounded Answer + Sources
```

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- Cohere API
- ChromaDB
- PyMuPDF
- python-docx
- Tesseract OCR

### Frontend

- React
- Vite
- JavaScript
- CSS

### Other

- Git
- GitHub
- REST API
- Retrieval-Augmented Generation (RAG)

## 📂 Project Structure

```text
DocRAG/
│
├── app/
│   ├── chunker.py
│   ├── document_processor.py
│   ├── main.py
│   ├── rag_pipeline.py
│   ├── vector_store.py
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
├── README.md
└── requirements.txt
```

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/tyagikanishka8-debug/DocRAG.git
cd DocRAG
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows:

```powershell
venv\Scripts\activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Cohere API key

Create a `.env` file in the project root:

```env
COHERE_API_KEY=your_cohere_api_key
```

Do not commit the `.env` file.

## ▶️ Run the Backend

```bash
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

API documentation is available at:

```text
http://localhost:8000/docs
```

## ▶️ Run the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open the local URL shown by Vite, usually:

```text
http://localhost:5173
```

## 💡 How RAG Works

1. Upload a document.
2. Extract text from PDF or DOCX.
3. Use OCR for scanned PDF pages when required.
4. Clean the extracted text.
5. Split the text into meaningful chunks.
6. Generate embeddings for the chunks.
7. Store embeddings in ChromaDB.
8. Convert the user's question into an embedding.
9. Retrieve relevant document chunks.
10. Send the retrieved context to the Cohere language model.
11. Generate a grounded answer.
12. Display the answer with source pages and snippets.

## 🔒 Grounded Answers

DocRAG is designed to answer questions using the retrieved document context rather than unsupported information.

If sufficient information cannot be found in the selected document, it responds:

> I couldn't find enough information in the selected document to answer that.

## 🔄 Conversation-Aware Questions

DocRAG supports follow-up questions by using previous conversation context to understand references such as:

- "What about this?"
- "What does it mean?"
- "How is it different?"
- "Tell me more about that."

The system rewrites follow-up questions into standalone questions before retrieving relevant document content.

## 📄 Document Management

DocRAG provides a document library that allows users to:

- View uploaded documents
- See file type and metadata
- See page and chunk counts
- Switch between documents
- Delete documents
- Prevent duplicate document uploads

## 🔍 Source Grounding

Each generated answer can include:

- Source document
- Page number
- Retrieved text snippet
- Relevance score
- Confidence indicator

This helps users understand where the answer came from.

## 🚀 Future Improvements

- Streaming AI responses
- Authentication and user accounts
- Cloud deployment
- More document formats
- Improved OCR processing
- Conversation persistence
- Advanced document analytics
- Production database integration

## 👩‍💻 Author

**Kanishka Tyagi**

B.Tech Computer Science & Engineering