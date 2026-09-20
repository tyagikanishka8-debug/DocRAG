import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(name="documents")

print("Total chunks:", collection.count())

results = collection.get(
    include=["metadatas"]
)

print("\nStored documents:")

seen_sources = set()

for metadata in results["metadatas"]:
    source = metadata["source"]

    if source not in seen_sources:
        print("-", source)
        seen_sources.add(source)

print("\nTotal unique documents:", len(seen_sources))