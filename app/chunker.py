def chunk_pages(pages, chunk_size=500, overlap=50):
    chunks = []

    for page in pages:
        text = page["text"]
        page_number = page["page"]

        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size

            chunk_text = text[start:end]

            chunks.append({
                "text": chunk_text,
                "page": page_number
            })

            start += chunk_size - overlap

    return chunks
if __name__ == "__main__":
    sample_pages = [
        {
            "text": "This is some text from page one. " * 20,
            "page": 1
        },
        {
            "text": "This is some text from page two. " * 20,
            "page": 2
        }
    ]

    chunks = chunk_pages(sample_pages, chunk_size=100, overlap=20)

    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}")
        print(f"Page: {chunk['page']}")
        print(f"Text: {chunk['text']}")