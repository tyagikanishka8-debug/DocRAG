import os
import cohere
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# Get Cohere API key
cohere_api_key = os.getenv("COHERE_API_KEY")

if not cohere_api_key:
    raise ValueError("Cohere API key not found!")


# Create Cohere client
co = cohere.ClientV2(
    api_key=cohere_api_key
)


def generate_embedding(text):
    response = co.embed(
        model="embed-v4.0",
        input_type="search_document",
        texts=[text],
        embedding_types=["float"]
    )

    return response.embeddings.float[0]


# Test embedding
if __name__ == "__main__":

    sample_text = "DocRAG is an AI system that answers questions from documents."

    embedding = generate_embedding(sample_text)

    print("Embedding generated successfully!")
    print("Embedding length:", len(embedding))
    print("First 5 values:", embedding[:5])