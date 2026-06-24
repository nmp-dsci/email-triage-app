from __future__ import annotations

from app.config import Settings


def build_model(settings: Settings):
    """Build the configured Pydantic AI model for non-mock providers.

    The imports stay local so the demo can still boot in mock mode if a provider
    package changes or credentials are absent.
    """
    if settings.llm_provider == "mock":
        return None

    from anthropic import AsyncAnthropic, AsyncAnthropicFoundry
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.providers.anthropic import AnthropicProvider

    if settings.llm_provider == "foundry":
        if not settings.azure_foundry_base_url or not settings.azure_foundry_api_key:
            raise RuntimeError("AZURE_FOUNDRY_BASE_URL and AZURE_FOUNDRY_API_KEY are required")
        client = AsyncAnthropicFoundry(
            base_url=settings.azure_foundry_base_url,
            api_key=settings.azure_foundry_api_key,
        )
    else:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    return AnthropicModel(
        settings.llm_model,
        provider=AnthropicProvider(anthropic_client=client),
    )
