def chunk_pages(
    pages,
    chunk_size=700,
    overlap=100
):
    """
    Split document pages into overlapping chunks.

    Tries to keep chunks around paragraph/sentence
    boundaries instead of cutting text randomly.
    """

    chunks = []

    for page in pages:

        text = page["text"].strip()
        page_number = page["page"]

        if not text:
            continue

        start = 0
        text_length = len(text)

        while start < text_length:

            end = min(
                start + chunk_size,
                text_length
            )

            # -----------------------------------
            # TRY TO FIND A NATURAL BREAK
            # -----------------------------------

            if end < text_length:

                paragraph_break = text.rfind(
                    "\n",
                    start,
                    end
                )

                sentence_break = text.rfind(
                    ". ",
                    start,
                    end
                )

                best_break = max(
                    paragraph_break,
                    sentence_break
                )

                if best_break > start + 300:

                    if (
                        paragraph_break
                        >= sentence_break
                    ):
                        end = paragraph_break + 1
                    else:
                        end = sentence_break + 1


            chunk_text = text[
                start:end
            ].strip()


            if chunk_text:

                chunks.append({

                    "text": chunk_text,

                    "page": page_number

                })


            # -----------------------------------
            # MOVE FORWARD WITH OVERLAP
            # -----------------------------------

            next_start = end - overlap

            if next_start <= start:
                next_start = end

            start = next_start


    return chunks


# -----------------------------------
# TEST
# -----------------------------------

if __name__ == "__main__":

    sample_pages = [

        {
            "text":
                "This is paragraph one. "
                * 30
                +
                "\n"
                +
                "This is paragraph two. "
                * 30,

            "page": 1
        },

        {
            "text":
                "This is page two content. "
                * 40,

            "page": 2
        }

    ]


    chunks = chunk_pages(
        sample_pages
    )


    for i, chunk in enumerate(
        chunks
    ):

        print(
            f"\nChunk {i + 1}"
        )

        print(
            f"Page: {chunk['page']}"
        )

        print(
            f"Length: {len(chunk['text'])}"
        )

        print(
            f"Text: {chunk['text'][:200]}"
        )