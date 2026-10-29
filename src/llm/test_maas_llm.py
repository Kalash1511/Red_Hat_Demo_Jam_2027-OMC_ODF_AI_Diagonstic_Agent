
import os

from dotenv import load_dotenv

from src.llm.maas_llm import MaaSLLM


def main():
    print("=" * 80)
    print("Red Hat MaaS LLM Configuration Test")
    print("=" * 80)

    load_dotenv()

    print("\n[1] Environment")
    print("-" * 80)

    api_key = os.getenv("MAAS_API_KEY")
    model = os.getenv("MAAS_MODEL")
    base_url = os.getenv("MAAS_API_BASE_URL")

    if not api_key:
        print("[FAIL] MAAS_API_KEY is not configured.")
        return

    print("[OK] MAAS_API_KEY is configured.")

    if model:
        print(f"[OK] MAAS_MODEL = {model}")
    else:
        print("[INFO] MAAS_MODEL not configured.")
        print(
            "[INFO] Default will be used: "
            "deepseek-r1-distill-qwen-14b"
        )

    if base_url:
        print(f"[OK] MAAS_API_BASE_URL = {base_url}")
    else:
        print("[INFO] MAAS_API_BASE_URL not configured.")
        print("[INFO] Default MaaS API URL will be used.")

    print("\n[2] Creating MaaS LLM")
    print("-" * 80)

    try:
        maas = MaaSLLM()

        print("[OK] MaaSLLM created successfully.")
        print(f"[OK] Model: {maas.model}")
        print(f"[OK] Base URL: {maas.base_url}")
        print(f"[OK] Temperature: {maas.temperature}")
        print(f"[OK] Max tokens: {maas.max_tokens}")

    except Exception as exc:
        print("[FAIL] Could not create MaaSLLM.")
        print(f"[ERROR] {exc}")
        return

    print("\n[3] Testing MaaS API")
    print("-" * 80)

    try:
        response = maas.get_llm().invoke(
            "Reply with exactly: MaaS connection successful."
        )

        print("[OK] MaaS API call successful.")
        print(f"\nResponse:\n{response.content}")

    except Exception as exc:
        print("[FAIL] MaaS API call failed.")
        print(f"[ERROR] {exc}")

    print("\n" + "=" * 80)
    print("MaaS LLM Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
