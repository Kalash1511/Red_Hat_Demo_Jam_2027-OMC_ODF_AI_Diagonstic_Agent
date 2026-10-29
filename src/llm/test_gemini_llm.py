import os

from dotenv import load_dotenv

from src.llm.gemini_llm import GeminiLLM


def main():
    print("=" * 80)
    print("Gemini LLM Configuration Test")
    print("=" * 80)

    load_dotenv()

    print("\n[1] Environment")
    print("-" * 80)

    api_key = os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GEMINI_MODEL")

    if not api_key:
        print("[FAIL] GOOGLE_API_KEY is not configured.")
        return

    print("[OK] GOOGLE_API_KEY is configured.")

    if model:
        print(f"[OK] GEMINI_MODEL = {model}")
    else:
        print("[INFO] GEMINI_MODEL not configured.")
        print("[INFO] Default will be used: gemini-2.5-flash")

    print("\n[2] Creating Gemini LLM")
    print("-" * 80)

    try:
        gemini = GeminiLLM()

        print("[OK] GeminiLLM created successfully.")
        print(f"[OK] Model: {gemini.model}")
        print(f"[OK] Temperature: {gemini.temperature}")

    except Exception as exc:
        print(f"[FAIL] Could not create GeminiLLM.")
        print(f"[ERROR] {exc}")
        return

    print("\n[3] Testing Gemini API")
    print("-" * 80)

    try:
        response = gemini.get_gemini_llm().invoke(
            "Reply with exactly: Gemini connection successful."
        )

        print("[OK] Gemini API call successful.")
        print(f"\nResponse:\n{response.content}")

    except Exception as exc:
        print("[FAIL] Gemini API call failed.")
        print(f"[ERROR] {exc}")

    print("\n" + "=" * 80)
    print("Gemini LLM Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()