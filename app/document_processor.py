import pymupdf
from docx import Document


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

if __name__ == "__main__":
    pdf_text = extract_text_from_pdf("uploads/sample.pdf")
    print("PDF TEXT:")
    print(pdf_text)

    docx_text = extract_text_from_docx("uploads/sample.docx")
    print("\nDOCX TEXT:")
    print(docx_text)

