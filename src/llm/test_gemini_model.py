import os

from dotenv import load_dotenv
from google import genai


def main():
    print("=" * 80)
    print("Available Gemini Models")
    print("=" * 80)

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("[FAIL] GOOGLE_API_KEY is not configured.")
        return

    print("[OK] GOOGLE_API_KEY is configured.")

    client = genai.Client(api_key=api_key)

    print("\nModels supporting generateContent:")
    print("-" * 80)

    try:
        for model in client.models.list():
            actions = getattr(model, "supported_actions", [])

            if "generateContent" in actions:
                print(model.name)

    except Exception as exc:
        print(f"[FAIL] Could not retrieve models.")
        print(f"[ERROR] {exc}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()