import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


class GroqLLM:
    """
    Configuration wrapper for the Groq LLM.
    """

    def __init__(self,model: str | None = None,temperature: float = 0.0,):
        load_dotenv()

        if not os.getenv("GROQ_API_KEY"):
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.model = model or os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

        self.temperature = temperature

        self.llm = ChatGroq(
            model=self.model,
            temperature=self.temperature,
            max_tokens=900,
        )

    def get_llm(self) -> ChatGroq:
        """
        Return the configured ChatGroq instance.
        """

        return self.llm

    