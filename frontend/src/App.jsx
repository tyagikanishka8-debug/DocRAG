import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "https://docrag-api.onrender.com";

function App() {
  const [documents, setDocuments] = useState([]);
  const [activeDocument, setActiveDocument] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [processingFile, setProcessingFile] = useState("");
  const [error, setError] = useState("");
  const [loadingAnswer, setLoadingAnswer] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loadingAnswer]);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/documents`);

      if (!response.ok) {
        throw new Error("Failed to load documents");
      }

      const data = await response.json();
      setDocuments(data.documents || []);

      if (!activeDocument && data.documents?.length > 0) {
        setActiveDocument(data.documents[0].filename);
      }
    } catch (err) {
      console.error(err);
      setError("Could not load documents.");
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const allowedTypes = [".pdf", ".docx"];
    const extension = file.name
      .substring(file.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowedTypes.includes(extension)) {
      setError("Please upload a PDF or DOCX file.");
      return;
    }

    setUploading(true);
    setProcessing(false);
    setProcessingFile(file.name);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setUploading(false);
      setProcessing(true);

      await fetchDocuments();

      pollProcessingStatus(file.name);
    } catch (err) {
      console.error(err);
      setUploading(false);
      setProcessing(false);
      setError(err.message || "Upload failed.");
    }

    event.target.value = "";
  };

  const pollProcessingStatus = async (filename) => {
    let attempts = 0;
    const maxAttempts = 120;

    const checkStatus = async () => {
      try {
        const response = await fetch(
          `${API_URL}/documents/${encodeURIComponent(filename)}/status`
        );

        if (!response.ok) {
          throw new Error("Could not check processing status");
        }

        const data = await response.json();

        if (data.status === "completed") {
          setProcessing(false);
          setProcessingFile("");
          setActiveDocument(filename);
          await fetchDocuments();
          return;
        }

        if (data.status === "failed") {
          setProcessing(false);
          setProcessingFile("");
          setError(data.error || "Document processing failed.");
          await fetchDocuments();
          return;
        }

        attempts += 1;

        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 1500);
        } else {
          setProcessing(false);
          setProcessingFile("");
          setError("Processing is taking longer than expected.");
        }
      } catch (err) {
        console.error(err);
        attempts += 1;

        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 1500);
        } else {
          setProcessing(false);
          setProcessingFile("");
          setError("Could not check document processing status.");
        }
      }
    };

    checkStatus();
  };

  const selectDocument = (filename) => {
    setActiveDocument(filename);
    setMessages([]);
    setQuestion("");
    setError("");
  };

  const deleteDocument = async (filename) => {
    const confirmed = window.confirm(
      `Delete "${filename}" from DocRAG?`
    );

    if (!confirmed) return;

    try {
      const response = await fetch(
        `${API_URL}/documents/${encodeURIComponent(filename)}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to delete document");
      }

      if (activeDocument === filename) {
        setActiveDocument("");
        setMessages([]);
      }

      await fetchDocuments();
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not delete document.");
    }
  };

  const askQuestion = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loadingAnswer) return;

    if (!activeDocument) {
      setError("Please select a document first.");
      return;
    }

    setError("");

    const userMessage = {
      role: "user",
      content: trimmedQuestion,
    };

    const conversationHistory = messages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoadingAnswer(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          source: activeDocument,
          conversation_history: conversationHistory,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to get answer");
      }

      const assistantMessage = {
        role: "assistant",
        content: data.answer || "No answer returned.",
        sources: data.sources || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error(err);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I couldn't process your question right now.",
          sources: [],
        },
      ]);

      setError(err.message || "Something went wrong.");
    } finally {
      setLoadingAnswer(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      askQuestion();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setQuestion("");
    setError("");
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "";

    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let index = 0;

    while (size >= 1024 && index < units.length - 1) {
      size /= 1024;
      index += 1;
    }

    return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="brand-area">
            <div className="brand-icon">✦</div>

            <div>
              <h1>DocRAG</h1>
              <p>AI-powered document intelligence</p>
            </div>
          </div>

          <div
            className={`header-badge ${
              activeDocument ? "ready" : ""
            }`}
          >
            <span className="status-dot"></span>
            {activeDocument ? "Document Ready" : "AI Document Assistant"}
          </div>
        </div>
      </header>

      <main className="main-container">
        <section className="hero-section">
          <div>
            <span className="hero-label">SMART DOCUMENT Q&A</span>

            <h2>
              Ask your documents.
              <span> Get answers.</span>
            </h2>

            <p>
              Upload your PDFs or DOCX files and let DocRAG
              find the information you need.
            </p>
          </div>

          <div className="hero-decoration">
            <div className="floating-card card-one">PDF</div>
            <div className="floating-card card-two">AI</div>
            <div className="floating-card card-three">Q&A</div>
          </div>
        </section>

        <section className="upload-card">
          <div className="upload-icon">↑</div>

          <div className="upload-content">
            <h3>Upload a document</h3>
            <p>PDF and DOCX supported</p>
          </div>

          <button
            className="upload-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || processing}
          >
            {uploading ? "Uploading..." : "Choose File"}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            onChange={handleUpload}
            hidden
          />
        </section>

        {processing && (
          <div className="processing-message">
            <div className="processing-spinner"></div>

            <div>
              <strong>Processing your document</strong>
              <p>
                {processingFile || "Your document"} is being
                analyzed in the background...
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <span>!</span>
            <p>{error}</p>

            <button onClick={() => setError("")}>×</button>
          </div>
        )}

        <section className="workspace">
          <aside className="sidebar">
            <div className="sidebar-header">
              <div>
                <span className="section-label">YOUR LIBRARY</span>
                <h3>Documents</h3>
              </div>

              <span className="document-count">
                {documents.length}
              </span>
            </div>

            {documents.length === 0 ? (
              <div className="empty-documents">
                <div className="empty-icon">📄</div>
                <p>No documents yet</p>
                <span>Upload a file to get started.</span>
              </div>
            ) : (
              <div className="document-list">
                {documents.map((document) => {
                  const isActive =
                    activeDocument === document.filename;

                  return (
                    <div
                      key={document.filename}
                      className={`document-item ${
                        isActive ? "active" : ""
                      }`}
                      onClick={() =>
                        selectDocument(document.filename)
                      }
                    >
                      <div className="document-icon">
                        {document.filename
                          .toLowerCase()
                          .endsWith(".docx")
                          ? "W"
                          : "P"}
                      </div>

                      <div className="document-info">
                        <strong title={document.filename}>
                          {document.filename}
                        </strong>

                        <div className="document-meta">
                          {document.pages || 0} pages
                          {document.chunks
                            ? ` • ${document.chunks} chunks`
                            : ""}
                        </div>
                      </div>

                      <button
                        className="delete-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          deleteDocument(document.filename);
                        }}
                        title="Delete document"
                      >
                        ×
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="sidebar-tip">
              <span>✦</span>
              <div>
                <strong>Pro tip</strong>
                <p>
                  Ask specific questions for more accurate
                  answers.
                </p>
              </div>
            </div>
          </aside>

          <section className="chat-section">
            <div className="chat-header">
              <div>
                <span className="section-label">AI ASSISTANT</span>

                <h3>
                  {activeDocument
                    ? "Chat with your document"
                    : "Select a document"}
                </h3>
              </div>

              {messages.length > 0 && (
                <button
                  className="clear-button"
                  onClick={clearChat}
                >
                  Clear Chat
                </button>
              )}
            </div>

            <div className="messages">
              {messages.length === 0 && (
                <div className="welcome-message">
                  <div className="welcome-icon">✦</div>

                  <h2>What would you like to know?</h2>

                  <p>
                    {activeDocument
                      ? `Ask anything about ${activeDocument}.`
                      : "Choose a document from your library to start asking questions."}
                  </p>

                  {activeDocument && (
                    <div className="suggestion-row">
                      <button
                        onClick={() =>
                          setQuestion("What is this document about?")
                        }
                      >
                        What is this document about?
                      </button>

                      <button
                        onClick={() =>
                          setQuestion("Summarize the main points.")
                        }
                      >
                        Summarize the main points
                      </button>
                    </div>
                  )}
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message ${message.role}`}
                >
                  <div className="message-avatar">
                    {message.role === "user" ? "You" : "✦"}
                  </div>

                  <div className="message-body">
                    <div className="message-label">
                      {message.role === "user"
                        ? "You"
                        : "DocRAG"}
                    </div>

                    <div className="message-content">
                      {message.content}
                    </div>

                    {message.role === "assistant" &&
                      message.sources?.length > 0 && (
                        <div className="sources">
                          <div className="sources-title">
                            <span>◈</span>
                            Sources
                          </div>

                          <p className="sources-explanation">
                            Relevance shows how closely the
                            retrieved text matches your
                            question. Confidence is DocRAG's
                            estimated confidence in the
                            retrieved information.
                          </p>

                          <div className="source-list">
                            {message.sources.map(
                              (source, sourceIndex) => (
                                <div
                                  className="source-item"
                                  key={sourceIndex}
                                >
                                  <div className="source-top">
                                    <div className="source-info">
                                      <strong>
                                        {source.filename ||
                                          source.source ||
                                          "Document"}
                                      </strong>

                                      {source.page && (
                                        <span>
                                          Page {source.page}
                                        </span>
                                      )}
                                    </div>

                                    {source.confidence && (
                                      <span
                                        className={`confidence-badge confidence-${String(
                                          source.confidence
                                        ).toLowerCase()}`}
                                      >
                                        {source.confidence}
                                      </span>
                                    )}
                                  </div>

                                  {source.relevance !==
                                    undefined && (
                                    <div className="relevance">
                                      <span>
                                        Relevance
                                      </span>

                                      <strong>
                                        {Number(
                                          source.relevance
                                        ).toFixed(1)}
                                        %
                                      </strong>
                                    </div>
                                  )}

                                  {source.snippet && (
                                    <div className="source-snippet">
                                      <span className="snippet-label">
                                        Retrieved text
                                      </span>

                                      <p>
                                        {source.snippet}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              ))}

              {loadingAnswer && (
                <div className="message assistant">
                  <div className="message-avatar">✦</div>

                  <div className="message-body">
                    <div className="message-label">
                      DocRAG
                    </div>

                    <div className="thinking">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef}></div>
            </div>

            <div className="question-area">
              <div className="question-box">
                <textarea
                  value={question}
                  onChange={(event) =>
                    setQuestion(event.target.value)
                  }
                  onKeyDown={handleKeyDown}
                  placeholder={
                    activeDocument
                      ? "Ask a question about your document..."
                      : "Select a document first..."
                  }
                  disabled={!activeDocument || loadingAnswer}
                  rows={1}
                />

                <button
                  className="send-button"
                  onClick={askQuestion}
                  disabled={
                    !activeDocument ||
                    !question.trim() ||
                    loadingAnswer
                  }
                  title="Ask question"
                >
                  ↑
                </button>
              </div>

              <div className="input-hint">
                <span>Enter to send</span>
                <span>•</span>
                <span>Answers are grounded in your document</span>
              </div>
            </div>
          </section>
        </section>
      </main>

      <footer>
        <span>DocRAG</span>
        <span>•</span>
        <span>AI-powered document Q&A</span>
      </footer>
    </div>
  );
}

export default App;