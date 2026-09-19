import pymupdf


def extract_text_from_pdf(file_path):
    document = pymupdf.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text
if __name__ == "__main__":
    text = extract_text_from_pdf("uploads/sample.pdf")
    print(text)