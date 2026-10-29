import os

from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_openai import ChatOpenAI


class MaaSLLM:
    """
    Configuration wrapper for the Red Hat MaaS LLM.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 900,
    ):
        load_dotenv()

        api_key = os.getenv("MAAS_API_KEY")

        if api_key is None or not api_key.strip():
            raise ValueError(
                "MAAS_API_KEY is not configured."
            )

        self.model = model or os.getenv(
            "MAAS_MODEL",
            "deepseek-r1-distill-qwen-14b",
        )

        self.base_url = os.getenv(
            "MAAS_API_BASE_URL",
            "https://maas-rhdp.apps.maas.redhatworkshops.io/v1",
        )

        self.temperature = temperature
        self.max_tokens = max_tokens

        self.llm = ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key=SecretStr(api_key),
            temperature=self.temperature,
            #max_tokens=self.max_tokens,
            timeout=120,
            max_retries=2,
            use_responses_api=False,
        )

    def get_llm(self) -> ChatOpenAI:
        """
        Return the configured MaaS LLM instance.
        """
        return self.llm
