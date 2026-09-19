import re


def clean_text(text):
    # Remove spaces at the beginning and end of each line
    lines = [line.strip() for line in text.splitlines()]

    # Remove empty lines
    lines = [line for line in lines if line]

    # Join the cleaned lines
    text = "\n".join(lines)

    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


if __name__ == "__main__":
    sample_text = """
    This    is     a document.


    It contains       unnecessary spaces.


    And unnecessary blank lines.
    """

    cleaned = clean_text(sample_text)

    print("CLEANED TEXT:")
    print(cleaned)