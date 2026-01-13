"""
Configuration management for the cookie flavor agent with multi-provider support.
"""
import os
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class AgentConfig(BaseModel):
    """Configuration for the cookie flavor agent with multi-provider support."""

    provider: Literal["anthropic", "databricks", "openai", "azure"] = Field(
        default="anthropic",
        description="LLM provider to use"
    )

    model_name: Optional[str] = Field(
        default=None,
        description="Model identifier (provider-specific defaults if None)"
    )

    api_key: Optional[str] = Field(
        default=None,
        description="API key for the provider"
    )

    endpoint: Optional[str] = Field(
        default=None,
        description="Custom endpoint URL (required for Databricks, Azure)"
    )

    workspace_dir: Optional[str] = Field(
        default=None,
        description="Directory for agent file operations"
    )

    auto_approve: bool = Field(
        default=False,
        description="Automatically approve agent actions"
    )

    verbose: bool = Field(
        default=True,
        description="Enable verbose logging"
    )

    @field_validator("model_name")
    @classmethod
    def set_default_model(cls, v, info):
        """Set provider-specific default models if not specified."""
        if v is None:
            provider = info.data.get("provider", "anthropic")
            defaults = {
                "anthropic": "claude-sonnet-4-5-20250929",
                "databricks": "databricks-claude-sonnet-4-5",
                "openai": "gpt-4-turbo",
                "azure": "gpt-4",
            }
            return defaults.get(provider)
        return v

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v, info):
        """Validate that endpoint is provided for providers that require it."""
        provider = info.data.get("provider")
        if provider in ["databricks", "azure"] and not v:
            # Check environment variables
            if provider == "databricks":
                v = os.getenv("DATABRICKS_HOST", "databricks")
            elif provider == "azure":
                v = os.getenv("AZURE_OPENAI_ENDPOINT")

            if not v and provider == "azure":
                raise ValueError(
                    f"Endpoint required for {provider} provider. "
                    f"Set via --endpoint flag or AZURE_OPENAI_ENDPOINT environment variable."
                )
        return v
