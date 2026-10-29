import os

from dotenv import load_dotenv
from groq import Groq


def main():
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    client = Groq(
        api_key=api_key
    )

    models = client.models.list()

    print("\n========== AVAILABLE GROQ MODELS ==========\n")

    for model in models.data:
        print(model.id)

    print(
        f"\nTotal models: {len(models.data)}"
    )


if __name__ == "__main__":
    main()