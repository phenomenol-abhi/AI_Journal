import os

from openai import OpenAI


class ProviderConfigError(Exception):
    pass


PROVIDER_SETTINGS = {
    "ollama": {
        "base_url": ("OLLAMA_API_BASE", "http://localhost:11434/v1"),
        "api_key": ("OLLAMA_API_KEY", "ollama"),
        "chat_model": ("OLLAMA_CHAT_MODEL", "llama3.1"),
        "embed_model": ("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    },
    "openrouter": {
        "base_url": ("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
        "api_key": ("OPENROUTER_API_KEY", None),
        "chat_model": ("OPENROUTER_CHAT_MODEL", "anthropic/claude-3.5-sonnet"),
        "embed_model": ("OPENROUTER_EMBED_MODEL", None),
    },
    "openai": {
        "base_url": ("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "api_key": ("OPENAI_API_KEY", None),
        "chat_model": ("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        "embed_model": ("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
    },
    "gemini": {
        "base_url": ("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai/"),
        "api_key": ("GEMINI_API_KEY", None),
        "chat_model": ("GEMINI_CHAT_MODEL", "gemini-2.0-flash"),
        "embed_model": ("GEMINI_EMBED_MODEL", "gemini-embedding-001"),
    },
}


class ProviderClient:
    def __init__(self, provider_name):
        settings = PROVIDER_SETTINGS.get(provider_name)
        if settings is None:
            raise ProviderConfigError(
                f"Unknown provider '{provider_name}'. Choose one of: {', '.join(PROVIDER_SETTINGS)}"
            )
        self.name = provider_name
        base_url_key, base_url_default = settings["base_url"]
        api_key_key, api_key_default = settings["api_key"]
        self.base_url = os.getenv(base_url_key, base_url_default)
        self.api_key = os.getenv(api_key_key, api_key_default)
        chat_model_key, chat_model_default = settings["chat_model"]
        embed_model_key, embed_model_default = settings["embed_model"]
        self.chat_model = os.getenv(chat_model_key, chat_model_default)
        self.embed_model = os.getenv(embed_model_key, embed_model_default)
        if self.api_key is None:
            raise ProviderConfigError(f"Missing API key for provider '{self.name}': set {api_key_key}")
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def chat(self, messages, stream=False, temperature=0.2):
        if not self.chat_model:
            raise ProviderConfigError(f"Provider '{self.name}' has no chat model configured")
        return self._client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            stream=stream,
            temperature=temperature,
        )

    def embed(self, texts):
        if not self.embed_model:
            raise ProviderConfigError(
                f"Provider '{self.name}' does not expose an embeddings endpoint. "
                "Set EMBED_PROVIDER to 'ollama' or 'openai' instead."
            )
        response = self._client.embeddings.create(model=self.embed_model, input=list(texts))
        return [item.embedding for item in response.data]


_chat_client = None
_embed_client = None


def resolve_provider(role):
    return os.getenv(f"{role}_PROVIDER", os.getenv("LLM_PROVIDER", "ollama"))


def get_chat_client():
    global _chat_client
    if _chat_client is None:
        _chat_client = ProviderClient(resolve_provider("CHAT"))
    return _chat_client


def get_embed_client():
    global _embed_client
    if _embed_client is None:
        _embed_client = ProviderClient(resolve_provider("EMBED"))
    return _embed_client
