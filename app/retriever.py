import os
import cohere
import chromadb
from dotenv import load_dotenv

load_dotenv()

cohere_api_key = os.getenv("COHERE_API_KEY")

if not cohere_api_key:
    raise ValueError("Cohere API key not found!")

co = cohere.ClientV2(api_key=cohere_api_key)

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(name="documents")


def generate_query_embedding(question):
    response = co.embed(
        model="embed-v4.0",
        input_type="search_query",
        texts=[question],
        embedding_types=["float"]
    )

    return response.embeddings.float[0]


def retrieve_chunks(question, top_k=5, distance_threshold=1.1):

    query_embedding = generate_query_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    filtered_documents = []
    filtered_metadatas = []
    filtered_distances = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        if distance <= distance_threshold:

            filtered_documents.append(document)
            filtered_metadatas.append(metadata)
            filtered_distances.append(distance)

    return (
        filtered_documents,
        filtered_metadatas,
        filtered_distances
    )


if __name__ == "__main__":

    question = input("Ask a question about your PDF: ")

    documents, metadatas, distances = retrieve_chunks(question)

    print("\nRELEVANT CHUNKS:\n")

    if not documents:

        print("No sufficiently relevant information found.")

    else:

        for i, (document, metadata, distance) in enumerate(
            zip(documents, metadatas, distances)
        ):

            print(f"\n--- Result {i + 1} ---")
            print(f"Distance: {distance:.4f}")
            print(f"Page: {metadata['page']}")
            print(f"Source: {metadata['source']}")
            print(f"Text:\n{document[:500]}")