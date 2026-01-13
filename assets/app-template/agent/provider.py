"""
Provider-specific LLM initialization with multi-provider support.
"""
import os
from typing import Optional


def get_llm_from_provider(
    provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    **kwargs
):
    """
    Get LLM instance based on provider.

    Supported providers:
    - anthropic: Claude models via Anthropic API
    - databricks: Models via Databricks Foundation Model API or Model Serving
    - openai: OpenAI models
    - azure: Azure OpenAI models

    Args:
        provider: Provider name (anthropic, databricks, openai, azure)
        model_name: Model identifier
        api_key: API key (provider-specific)
        endpoint: Custom endpoint URL (for Databricks, Azure)
        **kwargs: Additional provider-specific parameters

    Returns:
        LangChain LLM instance
    """
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            **kwargs
        )

    elif provider == "databricks":
        # Try to use the newer databricks-langchain package, fall back to langchain-community
        try:
            from databricks_langchain import ChatDatabricks
        except ImportError:
            from langchain_community.chat_models import ChatDatabricks

        # Databricks SDK authentication is handled automatically:
        # 1. Reads from ~/.databrickscfg (created by `databricks configure`)
        # 2. Uses DATABRICKS_CONFIG_PROFILE env var to select profile
        # 3. Falls back to DATABRICKS_HOST + DATABRICKS_TOKEN env vars
        # 4. Uses Azure/AWS/GCP instance metadata if available
        #
        # No need to pass api_key or token explicitly - SDK handles it all!

        # For Databricks Foundation Model API (managed models like Claude):
        # - The endpoint IS the model name (e.g., "databricks-claude-sonnet-4-5")
        # - This accesses /serving-endpoints/{model_name}/invocations
        #
        # For custom model serving endpoints:
        # - Pass a custom endpoint URL via the endpoint parameter
        return ChatDatabricks(
            endpoint=endpoint or model_name,  # Use model name as endpoint for foundation models
            **kwargs
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            **kwargs
        )

    elif provider == "azure":
        from langchain_openai import AzureChatOpenAI

        if api_key is None:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "Azure OpenAI API key required. Set AZURE_OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        if not endpoint:
            raise ValueError(
                "Azure OpenAI endpoint required. Set AZURE_OPENAI_ENDPOINT environment variable "
                "or pass endpoint parameter."
            )

        return AzureChatOpenAI(
            azure_endpoint=endpoint,
            deployment_name=model_name,
            api_key=api_key,
            api_version="2024-02-15-preview",
            **kwargs
        )

    else:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: anthropic, databricks, openai, azure"
        )
