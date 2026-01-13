"""
Application configuration management with multi-provider support.
"""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """
    Application configuration with environment variable support.

    Provides configuration for agent initialization with sensible defaults
    for Databricks provider.
    """

    # Agent configuration
    agent_provider: str = Field(
        default="databricks",
        env="AGENT_PROVIDER",
        description="LLM provider (databricks, anthropic, openai, azure)"
    )

    agent_model: Optional[str] = Field(
        default=None,
        env="AGENT_MODEL",
        description="Model name (provider-specific defaults if None)"
    )

    agent_workspace: str = Field(
        default="/tmp/agent-workspace",
        env="AGENT_WORKSPACE",
        description="Workspace directory for agent operations"
    )

    agent_auto_approve: bool = Field(
        default=True,
        env="AGENT_AUTO_APPROVE",
        description="Auto-approve agent actions (must be True for API)"
    )

    agent_endpoint: Optional[str] = Field(
        default=None,
        env="AGENT_ENDPOINT",
        description="Custom endpoint for Databricks/Azure"
    )

    # Databricks-specific configuration
    databricks_profile: Optional[str] = Field(
        default=None,
        env="DATABRICKS_PROFILE",
        description="Databricks CLI profile name from ~/.databrickscfg (e.g., 'DEFAULT', 'staging')"
    )

    databricks_host: Optional[str] = Field(
        default=None,
        env="DATABRICKS_HOST",
        description="Databricks workspace URL (optional, reads from profile if not set)"
    )

    @field_validator("agent_model", mode="before")
    @classmethod
    def set_default_model(cls, v, info):
        """Set provider-specific default model if not specified."""
        if v is None:
            provider = info.data.get("agent_provider", "databricks")
            defaults = {
                "databricks": "databricks-claude-sonnet-4-5",
                "anthropic": "claude-sonnet-4-5-20250929",
                "openai": "gpt-4-turbo",
                "azure": "gpt-4",
            }
            return defaults.get(provider, "databricks-claude-sonnet-4-5")
        return v

    @field_validator("agent_auto_approve")
    @classmethod
    def validate_auto_approve(cls, v):
        """Ensure auto_approve is True for API usage."""
        if not v:
            raise ValueError(
                "agent_auto_approve must be True for API usage. "
                "Interactive prompts cannot work in HTTP request context."
            )
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    def configure_databricks_environment(self) -> None:
        """
        Configure environment variables for Databricks SDK authentication.

        Sets the DATABRICKS_CONFIG_PROFILE environment variable if a profile
        is specified in the configuration. This allows the Databricks SDK to
        use credentials from the specified profile in ~/.databrickscfg.
        """
        if self.agent_provider != "databricks":
            return

        if self.databricks_profile:
            os.environ["DATABRICKS_CONFIG_PROFILE"] = self.databricks_profile


# Global configuration instance
config = AppConfig()
