"""
Core agent initialization and configuration with multi-provider support.
"""
from pathlib import Path
from typing import Optional

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from agent.provider import get_llm_from_provider


def get_skills_directory() -> str:
    """Get the absolute path to the skills directory."""
    current_dir = Path(__file__).parent
    skills_dir = current_dir / "skills"
    return str(skills_dir.absolute())


def get_system_prompt() -> str:
    """
    Load the system prompt from the system_prompt.md file.

    Returns:
        The system prompt string for agent initialization.
    """
    current_dir = Path(__file__).parent
    prompt_file = current_dir / "system_prompt.md"

    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove the markdown header if present
        lines = content.strip().split('\n')
        if lines and lines[0].startswith('# '):
            # Skip the header line and any empty lines after it
            content_lines = []
            skip_header = True
            for line in lines[1:]:
                if skip_header and line.strip() == '':
                    continue
                skip_header = False
                content_lines.append(line)
            return '\n'.join(content_lines).strip()

        return content.strip()

    except FileNotFoundError:
        raise RuntimeError(
            f"System prompt file not found: {prompt_file}. "
            "Please ensure system_prompt.md exists in the agent directory."
        )


def create_agent(
    provider: str = "anthropic",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    workspace_dir: Optional[str] = None,
    auto_approve: bool = False,
    **provider_kwargs
):
    """
    Create a deep agent with skills for marketing team product research.

    The agent has access to multiple skills including cookie flavor generation
    and can be extended with additional skills as needed.

    Supports multiple model providers: Anthropic, Databricks, OpenAI, Azure.

    Args:
        provider: Model provider (anthropic, databricks, openai, azure)
        model_name: Model identifier (required - should be provided by caller)
        api_key: API key for the provider
        endpoint: Custom endpoint (required for Databricks, Azure)
        workspace_dir: Directory for agent file operations (required)
        auto_approve: If True, automatically approve agent actions
        **provider_kwargs: Additional provider-specific parameters

    Returns:
        Configured deep agent instance
    """
    # Validate required parameters (config.py should always provide these)
    if model_name is None:
        raise ValueError(f"model_name is required for provider: {provider}")

    if workspace_dir is None:
        raise ValueError("workspace_dir is required")

    workspace_path = Path(workspace_dir)
    workspace_path.mkdir(exist_ok=True)

    # Get skills directory
    skills_dir = get_skills_directory()

    # Create LLM instance based on provider
    llm = get_llm_from_provider(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        endpoint=endpoint,
        **provider_kwargs
    )

    # Load system prompt from markdown file
    system_prompt = get_system_prompt()

    # Create the agent with skills
    # For API usage (auto_approve=True), interrupts are disabled (interrupt_on=None)
    # Note: virtual_mode=False allows skills to be read from the filesystem
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        skills=[skills_dir],
        backend=FilesystemBackend(
            root_dir=str(workspace_path),
            virtual_mode=False
        ),
        interrupt_on=None if auto_approve else {"task": True},
        name="marketing-research-agent",
    )

    return agent
