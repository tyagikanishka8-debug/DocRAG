import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [documents, setDocuments] = useState([]);
  const [activeDocument, setActiveDocument] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [question, setQuestion] = useState("");

  const [messages, setMessages] = useState([]);

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [processing, setProcessing] = useState(false);

  const [error, setError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");

  const chatEndRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, asking]);

  async function fetchDocuments() {
    try {
      const response = await fetch(
        `${API_URL}/documents`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load documents."
        );
      }

      const data = await response.json();

      setDocuments(data.documents || []);

      if (
        !activeDocument &&
        data.documents &&
        data.documents.length > 0
      ) {
        setActiveDocument(
          data.documents[0].filename
        );
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function checkProcessingStatus(
    filename
  ) {
    try {
      const response = await fetch(
        `${API_URL}/documents/${encodeURIComponent(
          filename
        )}/status`
      );

      if (!response.ok) {
        return null;
      }

      const data = await response.json();

      return data.status;
    } catch (err) {
      console.error(
        "Status check failed:",
        err
      );

      return null;
    }
  }

  async function waitForProcessing(
    filename
  ) {
    setProcessing(true);

    for (
      let attempt = 0;
      attempt < 120;
      attempt++
    ) {
      const status =
        await checkProcessingStatus(
          filename
        );

      if (status === "completed") {
        setProcessing(false);

        setUploadMessage(
          "✓ Document is ready! You can start asking questions."
        );

        await fetchDocuments();

        setActiveDocument(filename);

        return;
      }

      if (status === "failed") {
        setProcessing(false);

        setError(
          "Document processing failed. Please try uploading the file again."
        );

        return;
      }

      await new Promise(
        (resolve) =>
          setTimeout(resolve, 2000)
      );
    }

    setProcessing(false);

    setError(
      "Document processing is taking longer than expected. Please check again in a moment."
    );
  }

  async function handleUpload() {
    if (!selectedFile) {
      setError(
        "Please select a PDF or DOCX file first."
      );
      return;
    }

    setUploading(true);
    setError("");
    setUploadMessage("");
    setProcessing(false);

    const formData = new FormData();

    formData.append(
      "file",
      selectedFile
    );

    try {
      const response = await fetch(
        `${API_URL}/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Upload failed."
        );
      }

      if (data.status === "exists") {
        setUploadMessage(
          "This document is already uploaded."
        );

        await fetchDocuments();

        setActiveDocument(
          data.filename
        );

        setSelectedFile(null);

        return;
      }

      setUploadMessage(
        "File uploaded! DocRAG is processing your document in the background..."
      );

      setSelectedFile(null);

      await waitForProcessing(
        data.filename
      );
    } catch (err) {
      setError(
        err.message ||
          "Something went wrong while uploading."
      );
    } finally {
      setUploading(false);
    }
  }

  async function handleDeleteDocument(
    filename
  ) {
    const confirmed = window.confirm(
      `Delete "${filename}"? This will remove the document and its indexed data.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setUploadMessage("");

      const response = await fetch(
        `${API_URL}/documents/${encodeURIComponent(
          filename
        )}`,
        {
          method: "DELETE",
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to delete document."
        );
      }

      setDocuments((prev) =>
        prev.filter(
          (document) =>
            document.filename !== filename
        )
      );

      if (
        activeDocument === filename
      ) {
        setActiveDocument(null);
        setMessages([]);
      }

      setUploadMessage(
        `✓ ${filename} deleted successfully.`
      );
    } catch (err) {
      setError(
        err.message ||
          "Something went wrong while deleting the document."
      );
    }
  }

  async function handleAsk() {
    if (!question.trim()) {
      return;
    }

    if (!activeDocument) {
      setError(
        "Please upload or select a document first."
      );
      return;
    }

    const currentQuestion =
      question.trim();

    setQuestion("");
    setError("");
    setAsking(true);

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: currentQuestion,
      },
    ]);

    try {
      const response = await fetch(
        `${API_URL}/ask`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            question:
              currentQuestion,

            source:
              activeDocument,

            conversation_history:
              messages.map(
                (message) => ({
                  role:
                    message.role,

                  content:
                    message.content,
                })
              ),
          }),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to get an answer."
        );
      }

      setMessages((prev) => [
        ...prev,

        {
          role: "assistant",
          content: data.answer,
          sources:
            data.sources || [],
        },
      ]);

    } catch (err) {

      setError(
        err.message ||
          "Something went wrong while asking the question."
      );

    } finally {

      setAsking(false);
    }
  }

  function handleKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      if (
        !asking &&
        !processing
      ) {
        handleAsk();
      }
    }
  }

  function selectDocument(filename) {
    setActiveDocument(filename);
    setMessages([]);
    setError("");
    setUploadMessage("");
  }

  function clearChat() {
    setMessages([]);
    setError("");
  }

  return (
    <div className="app">

      <header className="header">

        <div className="header-content">

          <div>

            <h1>
              DocRAG
            </h1>

            <p>
              AI-powered document
              question answering
            </p>

          </div>

          <div
            className={`header-badge ${
              processing
                ? "processing"
                : activeDocument
                ? "ready"
                : ""
            }`}
          >

            {processing
              ? "⏳ Processing..."
              : activeDocument
              ? "✓ Document Ready"
              : "AI Document Assistant"}

          </div>

        </div>

      </header>


      <main className="main-container">

        <section className="upload-section">

          <div className="upload-card">

            <h2>
              Upload a document
            </h2>

            <p>
              Upload a PDF or DOCX and ask
              questions about its content.
            </p>

            <div className="upload-row">

              <input
                type="file"

                accept=".pdf,.docx"

                disabled={
                  uploading ||
                  processing
                }

                onChange={(event) => {

                  setSelectedFile(
                    event.target.files?.[0] ||
                      null
                  );

                  setError("");
                  setUploadMessage("");

                }}
              />

              <button
                onClick={handleUpload}

                disabled={
                  !selectedFile ||
                  uploading ||
                  processing
                }
              >

                {uploading
                  ? "Uploading..."
                  : "Upload Document"}

              </button>

            </div>

            {uploadMessage && (
              <div className="upload-message">
                {uploadMessage}
              </div>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

          </div>

        </section>


        {processing && (

          <div className="processing-message">

            <div className="processing-spinner">
              ⟳
            </div>

            <div>

              <strong>
                Processing your document...
              </strong>

              <p>
                DocRAG is extracting,
                chunking, embedding, and
                indexing your document.
                This may take a moment.
              </p>

            </div>

          </div>

        )}


        <section className="workspace">

          <aside className="sidebar">

            <div className="sidebar-header">

              <h2>
                Documents
              </h2>

              <span>
                {documents.length}
              </span>

            </div>


            {documents.length === 0 ? (

              <p className="empty-documents">
                No documents uploaded yet.
              </p>

            ) : (

              <div className="document-list">

                {documents.map(
                  (document) => (

                    <div
                      key={
                        document.filename
                      }

                      className={`document-item ${
                        activeDocument ===
                        document.filename
                          ? "active"
                          : ""
                      }`}
                    >

                      <button
                        className="document-select"

                        onClick={() =>
                          selectDocument(
                            document.filename
                          )
                        }

                        disabled={
                          processing
                        }
                      >

                        <span className="document-icon">

                          {document.file_type ===
                          ".docx"
                            ? "📝"
                            : "📄"}

                        </span>


                        <span className="document-details">

                          <span className="document-name">
                            {
                              document.filename
                            }
                          </span>

                          <span className="document-meta">

                            {document.file_type
                              ?.replace(
                                ".",
                                ""
                              )
                              .toUpperCase() ||
                              "FILE"}

                            {" • "}

                            {document.pages ??
                              0}

                            {" pages • "}

                            {document.chunks ??
                              0}

                            {" chunks"}

                          </span>

                        </span>

                      </button>


                      <button
                        className="delete-button"

                        onClick={() =>
                          handleDeleteDocument(
                            document.filename
                          )
                        }

                        disabled={
                          processing
                        }

                        title="Delete document"
                      >
                        🗑️
                      </button>

                    </div>
                  )
                )}

              </div>

            )}

          </aside>


          <section className="chat-section">

            <div className="chat-header">

              <div>

                <h2>
                  Ask your document
                </h2>

                <p>

                  {activeDocument
                    ? `Currently reading: ${activeDocument}`
                    : "Select a document to begin"}

                </p>

              </div>


              {messages.length > 0 && (

                <button
                  className="clear-button"

                  onClick={clearChat}

                  disabled={
                    asking ||
                    processing
                  }
                >
                  Clear Chat
                </button>

              )}

            </div>


            <div className="chat-container">

              {messages.length === 0 ? (

                <div className="empty-chat">

                  <div className="empty-icon">
                    💬
                  </div>

                  <h3>
                    Ask anything about
                    your document
                  </h3>

                  <p>
                    DocRAG will find the
                    relevant information
                    and generate an answer
                    using your document.
                  </p>

                </div>

              ) : (

                <div className="messages">

                  {messages.map(
                    (message, index) => (

                      <div
                        key={index}

                        className={`message ${
                          message.role
                        }`}
                      >

                        <div className="message-label">

                          {message.role ===
                          "user"
                            ? "You"
                            : "DocRAG"}

                        </div>


                        <div className="message-content">

                          {
                            message.content
                          }

                        </div>


                        {message.sources &&
                          message.sources
                            .length > 0 && (

                            <div className="sources">

                              <div className="sources-title">
                                Sources
                              </div>

                              <div className="sources-explanation">
                                Relevance shows how closely the retrieved text matches your question. Confidence is DocRAG's estimated confidence in the retrieved information.
                              </div>


                              {message.sources.map(
                                (
                                  source,
                                  sourceIndex
                                ) => (

                                  <div
                                    key={
                                      sourceIndex
                                    }

                                    className="source-item"
                                  >

                                    <div className="source-info">

                                      <span>
                                        📄
                                      </span>

                                      <span>

                                        {
                                          source.source
                                        }

                                        {" • Page "}

                                        {
                                          source.page
                                        }

                                      </span>

                                    </div>


                                    <div className="source-meta">

                                      {source.relevance !==
                                        undefined && (

                                        <span className="relevance-badge">

                                          {
                                            source.relevance
                                          }

                                          % relevant

                                        </span>

                                      )}


                                      {source.confidence && (

                                        <span
                                          className={`confidence-badge confidence-${source.confidence.toLowerCase()}`}
                                        >
                                          {source.confidence} confidence
                                        </span>

                                      )}

                                    </div>


                                    {source.snippet && (

                                      <div className="source-snippet">

                                        <span className="snippet-label">
                                          Retrieved text
                                        </span>

                                        <p>
                                          "{source.snippet}"
                                        </p>

                                      </div>

                                    )}

                                  </div>

                                )
                              )}

                            </div>

                          )}

                      </div>
                    )
                  )}


                  {asking && (

                    <div className="message assistant">

                      <div className="message-label">
                        DocRAG
                      </div>

                      <div className="thinking">

                        <span></span>
                        <span></span>
                        <span></span>

                      </div>

                    </div>

                  )}


                  <div
                    ref={chatEndRef}
                  />

                </div>

              )}

            </div>


            <div className="question-area">

              <textarea

                value={question}

                onChange={(event) =>
                  setQuestion(
                    event.target.value
                  )
                }

                onKeyDown={
                  handleKeyDown
                }

                placeholder={
                  processing
                    ? "Please wait while your document is being processed..."
                    : activeDocument
                    ? "Ask a question about your document..."
                    : "Upload a document first..."
                }

                disabled={
                  !activeDocument ||
                  asking ||
                  processing
                }

                rows={2}

              />


              <button

                onClick={handleAsk}

                disabled={
                  !question.trim() ||
                  !activeDocument ||
                  asking ||
                  processing
                }

              >

                {asking
                  ? "Thinking..."
                  : "Ask"}

              </button>

            </div>

          </section>

        </section>

      </main>

    </div>
  );
}

export default App;