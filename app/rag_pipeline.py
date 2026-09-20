import os

import cohere
import chromadb

from dotenv import load_dotenv


# -----------------------------------
# LOAD ENVIRONMENT
# -----------------------------------

load_dotenv()

cohere_api_key = os.getenv(
    "COHERE_API_KEY"
)

if not cohere_api_key:
    raise ValueError(
        "Cohere API key not found!"
    )


# -----------------------------------
# COHERE
# -----------------------------------

co = cohere.ClientV2(
    api_key=cohere_api_key
)


# -----------------------------------
# CHROMADB
# -----------------------------------

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_or_create_collection(
    name="documents"
)


# -----------------------------------
# QUERY EMBEDDING
# -----------------------------------

def generate_query_embedding(question):

    response = co.embed(
        model="embed-v4.0",
        input_type="search_query",
        texts=[question],
        embedding_types=["float"]
    )

    return response.embeddings.float[0]


# -----------------------------------
# REWRITE FOLLOW-UP QUESTION
# -----------------------------------

def rewrite_question(
    question,
    conversation_history
):

    if not conversation_history:
        return question

    history_text = ""

    for message in conversation_history[-6:]:

        role = message.get(
            "role",
            "user"
        )

        content = message.get(
            "content",
            ""
        )

        if content.strip():

            history_text += (
                f"{role.upper()}: "
                f"{content}\n"
            )

    prompt = f"""
You are a question rewriting assistant
for a document question-answering system.

Your task is to rewrite the user's latest
question into a standalone question.

Use the conversation history to resolve
references such as:

- it
- its
- they
- them
- this
- that
- these
- those
- the above
- the previous topic

STRICT RULES:

1. Preserve the user's original meaning.
2. Do not answer the question.
3. Do not add information that is not
   present in the conversation.
4. If the question is already standalone,
   return it unchanged.
5. Return ONLY the rewritten question.
6. Do not add explanations.

Conversation history:
{history_text}

Latest user question:
{question}

Standalone question:
"""

    response = co.chat(
        model="command-a-03-2025",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    rewritten_question = (
        response
        .message
        .content[0]
        .text
        .strip()
    )

    return rewritten_question


# -----------------------------------
# CONFIDENCE CALCULATION
# -----------------------------------

def get_confidence(relevance):

    if relevance >= 80:
        return "High"

    if relevance >= 60:
        return "Moderate"

    return "Low"


# -----------------------------------
# RETRIEVE CHUNKS
# -----------------------------------

def retrieve_chunks(
    question,
    source=None,
    top_k=5,
    distance_threshold=1.1
):

    query_embedding = generate_query_embedding(
        question
    )

    if source:

        results = collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=top_k,
            where={
                "source": source
            },
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

    else:

        results = collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=top_k,
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

    if (
        not results["documents"]
        or not results["documents"][0]
    ):

        return [], [], []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    filtered_documents = []
    filtered_metadatas = []
    filtered_distances = []

    for (
        document,
        metadata,
        distance
    ) in zip(
        documents,
        metadatas,
        distances
    ):

        if distance <= distance_threshold:

            filtered_documents.append(
                document
            )

            metadata = metadata.copy()

            metadata["distance"] = round(
                float(distance),
                4
            )

            relevance = max(
                0,
                min(
                    100,
                    (1 - distance) * 100
                )
            )

            relevance = round(
                relevance,
                1
            )

            metadata["relevance"] = relevance

            metadata["confidence"] = (
                get_confidence(
                    relevance
                )
            )

            snippet = document.strip()

            if len(snippet) > 300:

                snippet = (
                    snippet[:300]
                    + "..."
                )

            metadata["snippet"] = snippet

            filtered_metadatas.append(
                metadata
            )

            filtered_distances.append(
                distance
            )

    return (
        filtered_documents,
        filtered_metadatas,
        filtered_distances
    )


# -----------------------------------
# GENERATE ANSWER
# -----------------------------------

def generate_answer(
    question,
    documents,
    conversation_history=None
):

    # -----------------------------------
    # NO RELEVANT INFORMATION
    # -----------------------------------

    if not documents:

        return (
            "I couldn't find enough information "
            "in the selected document to answer that."
        )

    context = "\n\n".join(
        documents
    )

    conversation_text = ""

    if conversation_history:

        for message in conversation_history[-6:]:

            role = message.get(
                "role",
                "user"
            )

            content = message.get(
                "content",
                ""
            )

            if content.strip():

                conversation_text += (
                    f"{role.upper()}: "
                    f"{content}\n"
                )

    prompt = f"""
You are DocRAG, an AI assistant that answers
questions using ONLY the provided document
context.

Your job is to give accurate, grounded answers.

STRICT RULES:

1. Use ONLY the provided document context
   to answer the current question.

2. Do NOT use outside knowledge, general
   knowledge, assumptions, or guesses.

3. Do NOT invent facts, names, dates,
   numbers, explanations, or examples.

4. Conversation history may ONLY be used
   to understand references such as "it",
   "they", "this", or "the previous topic".

5. The conversation history is NOT a source
   of factual information. Facts must come
   from the document context.

6. If the document context does not contain
   enough information to answer the question,
   respond EXACTLY with:

"I couldn't find enough information in the selected document to answer that."

7. If only part of the question can be
   answered from the document, answer only
   the supported part and clearly state that
   the remaining information was not found.

8. Never pretend that missing information
   exists in the document.

9. Keep answers clear, direct, and concise.

10. Do not mention embeddings, vector
    databases, retrieval, prompts, or the
    internal DocRAG system.

Conversation history:
{conversation_text}

Document context:
{context}

Current question:
{question}

Answer:
"""

    response = co.chat(
        model="command-a-03-2025",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = (
        response
        .message
        .content[0]
        .text
        .strip()
    )

    return answer


# -----------------------------------
# ASK QUESTION
# -----------------------------------

def ask_question(
    question,
    source=None,
    conversation_history=None
):

    if conversation_history is None:
        conversation_history = []

    standalone_question = rewrite_question(
        question,
        conversation_history
    )

    (
        documents,
        metadatas,
        distances
    ) = retrieve_chunks(
        standalone_question,
        source=source
    )

    answer = generate_answer(
        standalone_question,
        documents,
        conversation_history
    )

    return answer, metadatas