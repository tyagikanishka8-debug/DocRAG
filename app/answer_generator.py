import os
import cohere
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# Get Cohere API key
cohere_api_key = os.getenv("COHERE_API_KEY")

if not cohere_api_key:
    raise ValueError("Cohere API key not found!")


# Create Cohere client
co = cohere.ClientV2(
    api_key=cohere_api_key
)


def generate_answer(question, context):
    """
    Generate an answer using the retrieved document context.
    """

    prompt = f"""
You are DocRAG, an AI assistant that answers questions
using information from the provided document.

Answer the user's question using ONLY the context below.

If the answer cannot be found in the context, say:
"I couldn't find the answer in the document."

Do not make up information.

Context:
{context}

Question:
{question}

Answer:
"""

    response = co.chat(
        model="command-a-03-2025",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content[0].text


if __name__ == "__main__":

    question = "What is an abstract noun?"

    context = """
    Abstract Noun:
    It is usually the name of a quality, action or state.
    Examples: Goodness, Honesty, Bravery, Wisdom,
    Darkness, Laughter, Childhood and Poverty.
    """

    answer = generate_answer(
        question,
        context
    )

    print("\nANSWER:")
    print(answer)