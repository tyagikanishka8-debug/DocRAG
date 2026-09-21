import os
import cohere
from dotenv import load_dotenv
from app.vector_store import search_similar

load_dotenv()

co = cohere.Client(os.getenv("COHERE_API_KEY"))


def rewrite_question(question, conversation_history=None):
    """
    Rewrite a follow-up question into a standalone question
    using the previous conversation when needed.
    """

    if not conversation_history:
        return question

    history_text = ""

    for message in conversation_history[-6:]:
        role = message.get("role", "user")
        content = message.get("content", "")
        history_text += f"{role}: {content}\n"

    prompt = f"""
Rewrite the user's latest question as a standalone question.

Use the conversation history only to resolve references such as:
- it
- this
- that
- they
- the above
- the previous topic

Do not add information that is not present in the conversation.

Conversation history:
{history_text}

Latest question:
{question}

Return only the rewritten standalone question.
"""

    try:
        response = co.chat(
            model="command-a-03-2025",
            message=prompt
        )

        rewritten = response.text.strip()

        if rewritten:
            return rewritten

    except Exception:
        pass

    return question


def get_confidence(relevance):
    """
    Convert relevance score into a simple confidence label.
    """

    if relevance >= 80:
        return "High"

    if relevance >= 60:
        return "Moderate"

    return "Low"


def ask_question(
    question,
    source="all",
    conversation_history=None
):
    """
    Complete RAG pipeline:

    1. Rewrite follow-up question
    2. Retrieve relevant chunks
    3. Filter extremely weak results
    4. Generate grounded answer
    5. Return answer + sources
    """

    standalone_question = rewrite_question(
        question,
        conversation_history
    )

    # Retrieve more candidates so production retrieval
    # has enough context to work with.
    results = search_similar(
        standalone_question,
        source=source,
        n_results=5
    )

    if not results:
        return {
            "answer": "I couldn't find enough information in the selected document to answer that.",
            "sources": []
        }

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "answer": "I couldn't find enough information in the selected document to answer that.",
            "sources": []
        }

    # Keep reasonably relevant chunks.
    # ChromaDB cosine distance: lower = more similar.
    filtered = []

    for i, document in enumerate(documents):

        distance = distances[i] if i < len(distances) else 1.0

        # More forgiving production threshold.
        if distance <= 1.5:
            filtered.append({
                "document": document,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distance
            })

    # If the threshold removed everything, keep the best
    # retrieved result instead of throwing away all context.
    if not filtered:
        best_index = 0

        best_distance = (
            distances[0]
            if distances
            else 1.0
        )

        for i, distance in enumerate(distances):
            if distance < best_distance:
                best_distance = distance
                best_index = i

        filtered.append({
            "document": documents[best_index],
            "metadata": (
                metadatas[best_index]
                if best_index < len(metadatas)
                else {}
            ),
            "distance": best_distance
        })

    context_parts = []
    sources = []

    for item in filtered:

        document = item["document"]
        metadata = item["metadata"]
        distance = item["distance"]

        # Convert ChromaDB distance into a simple relevance score.
        relevance = max(
            0,
            min(
                100,
                round((1 - distance / 1.5) * 100, 1)
            )
        )

        confidence = get_confidence(relevance)

        context_parts.append(document)

        snippet = document[:300]

        sources.append({
            "filename": metadata.get("filename", "Unknown"),
            "page": metadata.get("page", "Unknown"),
            "relevance": relevance,
            "confidence": confidence,
            "snippet": snippet
        })

    context = "\n\n---\n\n".join(context_parts)

    history_text = ""

    if conversation_history:
        for message in conversation_history[-6:]:
            role = message.get("role", "user")
            content = message.get("content", "")
            history_text += f"{role}: {content}\n"

    prompt = f"""
You are DocRAG, a document question-answering assistant.

Answer the user's question using ONLY the information contained
in the provided document context.

Rules:

1. Do not use outside knowledge.
2. Do not guess or invent facts.
3. If the document does not contain enough information,
   say exactly:
   "I couldn't find enough information in the selected document to answer that."
4. You may combine information from multiple retrieved sections
   when they support the answer.
5. If only part of the question is supported, answer only that part
   and clearly state that the remaining information was not found.
6. Conversation history may be used only to understand references
   in the user's question. It must NOT be used as a source of facts.
7. Give a clear and concise answer.
8. Do not mention the retrieval process unless necessary.

Conversation history:
{history_text}

Document context:
{context}

User question:
{question}

Answer:
"""

    try:
        response = co.chat(
            model="command-a-03-2025",
            message=prompt
        )

        answer = response.text.strip()

    except Exception:
        answer = (
            "I couldn't generate an answer right now. "
            "Please try again."
        )

    return {
        "answer": answer,
        "sources": sources
    }