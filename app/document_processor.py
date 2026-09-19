import pymupdf
import pytesseract
from PIL import Image
from docx import Document

from chunker import chunk_pages

# Tell pytesseract where Tesseract is installed
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# -----------------------------------
# PDF TEXT EXTRACTION
# -----------------------------------

def extract_text_from_pdf(file_path):
    document = pymupdf.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


# -----------------------------------
# PDF PAGE EXTRACTION
# -----------------------------------

def extract_pages_from_pdf(file_path):
    document = pymupdf.open(file_path)

    pages = []

    for page_number, page in enumerate(document):
        text = page.get_text()

        pages.append({
            "text": text,
            "page": page_number + 1
        })

    document.close()

    return pages


# -----------------------------------
# DOCX TEXT EXTRACTION
# -----------------------------------

def extract_text_from_docx(file_path):
    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


# -----------------------------------
# OCR EXTRACTION
# -----------------------------------

def extract_text_with_ocr(file_path):
    document = pymupdf.open(file_path)

    text = ""

    for page in document:
        pixmap = page.get_pixmap()

        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples
        )

        text += pytesseract.image_to_string(image)
        text += "\n"

    document.close()

    return text


# -----------------------------------
# AUTOMATIC PDF EXTRACTION
# -----------------------------------

def extract_text_from_pdf_auto(file_path):
    text = extract_text_from_pdf(file_path)

    if len(text.strip()) > 50:
        return text

    print("Very little text found. Using OCR...")

    return extract_text_with_ocr(file_path)


# -----------------------------------
# TEST THE COMPLETE PIPELINE
# -----------------------------------

if __name__ == "__main__":

    # Extract pages from the PDF
    pages = extract_pages_from_pdf("uploads/sample.pdf")

    # Create chunks while keeping page numbers
    pdf_chunks = chunk_pages(pages)

    # Display the first 10 chunks
    print("\nPDF CHUNKS:")

    for i, chunk in enumerate(pdf_chunks[:10]):
        print(f"\nChunk {i + 1}")
        print(f"Page: {chunk['page']}")
        print(f"Text: {chunk['text'][:200]}")