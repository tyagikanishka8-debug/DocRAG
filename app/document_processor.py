import pymupdf
import pytesseract
from PIL import Image
from docx import Document
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_pdf(file_path):
    document = pymupdf.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


def extract_text_from_docx(file_path):
    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


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

def extract_text_from_pdf_auto(file_path):
    text = extract_text_from_pdf(file_path)

    if len(text.strip()) > 50:
        return text

    print("Very little text found. Using OCR...")
    return extract_text_with_ocr(file_path)


if __name__ == "__main__":
    pdf_text = extract_text_from_pdf("uploads/sample.pdf")
    print("PDF TEXT:")
    print(pdf_text)

    docx_text = extract_text_from_docx("uploads/sample.docx")
    print("\nDOCX TEXT:")
    print(docx_text)

    auto_text = extract_text_from_pdf_auto("uploads/sample.pdf")
    print("\nAUTO PDF TEXT:")
    print(auto_text)
    