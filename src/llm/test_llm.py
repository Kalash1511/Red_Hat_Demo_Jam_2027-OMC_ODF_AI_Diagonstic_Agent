from src.llm import GroqLLM


def main():

    llm = GroqLLM()

    print("Model:", llm.model)

    response = llm.get_llm().invoke(
        "Respond with exactly: LLM connection successful"
    )

    print("Response:")
    print(response.content)


if __name__ == "__main__":
    main()