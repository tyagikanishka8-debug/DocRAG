import os
import chromadb
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# Get the Cohere API key
cohere_api_key = os.getenv("COHERE_API_KEY")


# Create a persistent ChromaDB client
client = chromadb.PersistentClient(
    path="chroma_db"
)


# Create or get our document collection
collection = client.get_or_create_collection(
    name="documents"
)


# Check whether the Cohere API key exists
if cohere_api_key:
    print("Cohere API key loaded successfully!")
else:
    print("Cohere API key not found!")


print("ChromaDB collection created successfully!")
print("Collection name:", collection.name)