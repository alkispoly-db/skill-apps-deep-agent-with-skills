# Deep Agent Application Architecture

Architecture overview for Databricks deep agent applications.

## Overview

A deep agent system using the deepagents library with multi-provider support. The agent integrates with FastAPI to provide an OpenAI-compatible API for chat completions.

## Project Structure

```
app/
├── app.py                      # FastAPI application with agent
├── config.py                   # Main application configuration
├── routes/
│   └── v1/
│       ├── completions.py      # OpenAI-compatible chat endpoint
│       └── healthcheck.py      # Health check endpoint
├── models/
│   └── openai_schema.py        # Pydantic models
└── agent/
    ├── __init__.py
    ├── core.py                 # Agent creation and initialization
    ├── provider.py             # Multi-provider LLM support
    ├── system_prompt.md        # System prompt (easy to edit)
    └── skills/
        └── skill-name/
            ├── SKILL.md
            └── references/
                └── reference-docs.md
```

## Supported Providers

### 1. Databricks (Default: `databricks-claude-sonnet-4-5`)
- Uses Databricks SDK for authentication
- Supports Foundation Model API and Model Serving endpoints
- Available models:
  - `databricks-claude-sonnet-4-5` (default)
  - `databricks-meta-llama-3-1-405b-instruct`
  - `databricks-meta-llama-3-1-70b-instruct`
  - `databricks-meta-llama-3-1-8b-instruct`
  - `databricks-dbrx-instruct`
  - `databricks-mixtral-8x7b-instruct`

### 2. Anthropic (Default: `claude-sonnet-4-5-20250929`)
- Direct Claude API integration
- Requires ANTHROPIC_API_KEY

### 3. OpenAI (Default: `gpt-4-turbo`)
- OpenAI API integration
- Requires OPENAI_API_KEY

### 4. Azure (Default: `gpt-4`)
- Azure OpenAI integration
- Requires AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT

## Configuration

### Environment Variables

**Provider Selection:**
```bash
AGENT_PROVIDER=databricks           # or anthropic, openai, azure
AGENT_MODEL=databricks-claude-sonnet-4-5
AGENT_AUTO_APPROVE=true
AGENT_WORKSPACE=/tmp/agent-workspace
```

**Databricks:**
```bash
DATABRICKS_HOST="https://your-workspace.databricks.com"
DATABRICKS_TOKEN="your-token"
DATABRICKS_PROFILE=DEFAULT          # For Databricks CLI auth
```

**Anthropic:**
```bash
ANTHROPIC_API_KEY="your-api-key"
```

**OpenAI:**
```bash
OPENAI_API_KEY="your-api-key"
```

**Azure:**
```bash
AZURE_OPENAI_API_KEY="your-api-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
```

### Configuration Management

Configuration is managed via Pydantic Settings with automatic environment variable loading:

```python
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    agent_provider: str = "databricks"
    agent_model: str = None  # Auto-set based on provider
    agent_auto_approve: bool = False
    agent_workspace: str = "/tmp/agent-workspace"

    databricks_host: Optional[str] = None
    databricks_token: Optional[str] = None
    databricks_profile: str = "DEFAULT"

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
```

## Skills System

### Progressive Disclosure Pattern

Skills follow a three-level loading pattern:

1. **Level 1: Metadata** - Frontmatter in SKILL.md (name, description)
2. **Level 2: Instructions** - Full SKILL.md content
3. **Level 3: Resources** - Reference materials in references/ directory

### Skill Structure

```
skill-name/
├── SKILL.md                    # Main skill definition
├── scripts/                    # Optional automation scripts
│   └── helper.py
└── references/                 # Optional reference materials
    └── deep-knowledge.md
```

### SKILL.md Format

```markdown
---
name: skill-name
description: Brief description of what the skill does and when to use it
---

# Skill Title

## Usage

[Instructions for using this skill]

## Examples

[Usage examples]
```

### Skill Discovery

Skills are automatically loaded from the `agent/skills/` directory:

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

agent = create_deep_agent(
    model=llm,
    system_prompt=system_prompt,
    skills=[skills_dir],  # Path to skills directory
    backend=FilesystemBackend(
        root_dir=workspace_path,
        virtual_mode=False  # Enable filesystem skill discovery
    ),
    interrupt_on=None if auto_approve else {"task": True},
    name="agent-name"
)
```

## FastAPI Integration

### Application Lifespan Management

The agent is initialized once at startup and shared across requests:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize agent at startup
    logger.info("============================================================")
    logger.info("Initializing Agent")
    logger.info("============================================================")

    agent = create_agent(
        provider=config.agent_provider,
        model_name=config.agent_model,
        workspace_dir=config.agent_workspace,
        auto_approve=config.agent_auto_approve,
        databricks_profile=config.databricks_profile
    )

    app.state.agent = agent  # Shared instance
    logger.info("Agent initialized successfully!")

    yield

    # Cleanup on shutdown (if needed)
    logger.info("Shutting down agent")

app = FastAPI(lifespan=lifespan)
```

### Dependency Injection

The agent is accessed via FastAPI dependency injection:

```python
from fastapi import Depends, Request

def get_agent(request: Request):
    """Get the shared agent instance from application state."""
    if not hasattr(request.app.state, "agent"):
        raise RuntimeError("Agent not initialized")
    return request.app.state.agent

@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    agent = Depends(get_agent)
):
    # Use agent here
    result = agent.invoke({"messages": messages})
```

### OpenAI-Compatible API

The completions endpoint provides OpenAI-compatible format:

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

**Response:**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response text..."
      },
      "finish_reason": "stop"
    }
  ]
}
```

## Multi-Provider Architecture

### Provider Factory Pattern

The `get_llm_from_provider` function in `agent/provider.py` creates provider-specific LLM instances:

```python
def get_llm_from_provider(
    provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    **provider_kwargs
):
    """
    Create LLM instance based on provider.

    Args:
        provider: Provider name (databricks, anthropic, openai, azure)
        model_name: Model identifier
        api_key: API key for provider
        endpoint: Custom endpoint (required for Databricks, Azure)
        **provider_kwargs: Additional provider-specific parameters

    Returns:
        LangChain LLM instance
    """
    if provider == "databricks":
        return create_databricks_llm(model_name, endpoint, **provider_kwargs)
    elif provider == "anthropic":
        return create_anthropic_llm(model_name, api_key)
    elif provider == "openai":
        return create_openai_llm(model_name, api_key)
    elif provider == "azure":
        return create_azure_llm(model_name, api_key, endpoint)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
```

### Databricks Authentication

Databricks apps automatically provide authentication via environment variables:

```python
from databricks.sdk import WorkspaceClient
from langchain_community.chat_models import ChatDatabricks

# Option 1: Automatic (Databricks Apps)
# DATABRICKS_HOST and DATABRICKS_TOKEN provided by platform

# Option 2: CLI Profile
w = WorkspaceClient(profile="DEFAULT")

# Option 3: Explicit credentials
w = WorkspaceClient(
    host=os.getenv("DATABRICKS_HOST"),
    token=os.getenv("DATABRICKS_TOKEN")
)

llm = ChatDatabricks(
    target_uri="databricks",
    endpoint=model_name,
    temperature=0.1
)
```

## Agent Features

### Auto-Approve Mode

When `auto_approve=True`, the agent runs without user interrupts:

```python
agent = create_deep_agent(
    model=llm,
    system_prompt=system_prompt,
    skills=[skills_dir],
    backend=backend,
    interrupt_on=None if auto_approve else {"task": True},
    name="agent-name"
)
```

- **API usage:** Always use `auto_approve=True`
- **Interactive mode:** Use `auto_approve=False` for user confirmations

### System Prompt Customization

System prompts are stored in `agent/system_prompt.md` for easy editing:

```python
def get_system_prompt() -> str:
    """Load the system prompt from the system_prompt.md file."""
    prompt_file = Path(__file__).parent / "system_prompt.md"

    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove markdown header if present
    lines = content.strip().split('\n')
    if lines and lines[0].startswith('# '):
        content = '\n'.join(lines[1:]).strip()

    return content
```

### Workspace Management

The agent uses a filesystem backend for file operations:

```python
workspace_path = Path(workspace_dir)
workspace_path.mkdir(exist_ok=True)

backend = FilesystemBackend(
    root_dir=str(workspace_path),
    virtual_mode=False  # Allow reading skills from filesystem
)
```

- `virtual_mode=False`: Agent can read skills from `agent/skills/`
- `virtual_mode=True`: Agent restricted to workspace directory only

## Deployment Architecture

### Databricks Apps Platform

```
Databricks Apps Platform
├── Container Runtime
│   ├── Python 3.11
│   ├── FastAPI App (port 8000)
│   └── Dependencies from requirements.txt
│
├── Service Principal Identity
│   ├── Auto-configured DATABRICKS_HOST
│   └── Auto-configured DATABRICKS_TOKEN
│
├── Agent System
│   ├── Databricks Foundation Model API
│   │   └── databricks-claude-sonnet-4-5
│   ├── Skills
│   │   └── skill-name/
│   └── System Prompt (agent/system_prompt.md)
│
└── API Endpoints
    ├── / (root with API info)
    ├── /docs (interactive API docs)
    ├── /api/v1/healthcheck
    └── /api/v1/chat/completions
```

### app.yaml Configuration

```yaml
command: ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

env:
  - name: AGENT_PROVIDER
    value: "databricks"
  - name: AGENT_MODEL
    value: "databricks-claude-sonnet-4-5"
  - name: AGENT_AUTO_APPROVE
    value: "true"
  - name: AGENT_WORKSPACE
    value: "/tmp/agent-workspace"
```

**Key Points:**
- Port 8000 is required by Databricks Apps
- Environment variables configure the agent
- `DATABRICKS_HOST` and `DATABRICKS_TOKEN` automatically provided

## Best Practices

### 1. Configuration Management
- Use environment variables for all configuration
- Provide sensible defaults based on provider
- Validate configuration at startup

### 2. Error Handling
- Catch provider-specific authentication errors
- Validate skill structure before loading
- Provide clear error messages

### 3. Skill Development
- Keep SKILL.md concise and actionable
- Use references/ for detailed documentation
- Follow progressive disclosure pattern

### 4. Testing
- Test locally before deploying
- Use interactive chat client for manual testing
- Validate OpenAI compatibility

### 5. Monitoring
- Log agent initialization details
- Track request/response patterns
- Monitor model usage and costs

## Performance Considerations

### Single Agent Instance
- Agent initialized once at startup
- Shared across all requests
- Efficient resource usage

### Workspace Directory
- Use temporary directory (`/tmp/agent-workspace`)
- Clean up periodically if needed
- Consider persistent storage for file operations

### Model Selection
- Choose models based on task complexity
- Balance cost vs. capability
- Test with smaller models first

## Security Considerations

### Authentication
- Databricks Apps: Automatic via platform
- External APIs: Store credentials securely
- Never commit API keys to version control

### Input Validation
- Validate all user inputs
- Sanitize file paths
- Limit message sizes

### Skill Permissions
- Review skill code before deploying
- Limit filesystem access
- Monitor skill execution
