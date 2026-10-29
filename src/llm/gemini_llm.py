import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiLLM:
    """
    Configuration wrapper for the Google Gemini LLM.
    """

    def __init__(self,model: str | None = None,temperature: float = 0.0,):
        load_dotenv()

        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError(
                "GOOGLE_API_KEY is not configured."
            )

        self.model = model or os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        self.temperature = temperature

        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=900,
            max_retries=2,
        )

    def get_gemini_llm(self) -> ChatGoogleGenerativeAI:
        """
        Return the configured ChatGoogleGenerativeAI instance.
        """
        return self.llm