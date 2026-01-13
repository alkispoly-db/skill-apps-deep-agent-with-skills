---
name: databricks-deep-agent-app
description: Generate customized Databricks applications for deep agents with configurable system prompts and skills. Use when you need to create a FastAPI app that deploys to Databricks and runs a deep agent with custom prompts and domain-specific skills. Supports (1) Custom system prompt configuration (2) Adding existing skills or creating new ones (3) Complete app generation with OpenAI-compatible API (4) Automated Databricks deployment and testing.
---

# Databricks Deep Agent App Generator

Generate production-ready Databricks applications for deep agents with custom system prompts and skills.

## Interactive Workflow

When the user requests a Databricks deep agent app, follow this interactive workflow:

### Step 1: Gather Requirements

Use AskUserQuestion to gather key information:

1. **App name** - What to call the app (e.g., "cooking-recipe-agent", "sql-assistant")
2. **System prompt** - The deep agent's specialized instructions and capabilities
3. **Skills to include** - Whether to add existing skills or create new ones

**Example interaction:**
```
User: "I want to create a databricks app that runs an agent to generate cooking recipes"

Use AskUserQuestion to gather:
- App name (propose: "cooking-recipe-agent")
- System prompt (propose a template based on the domain)
- Whether to include skills (yes/no)
```

### Step 2: Generate the App

Once you have the requirements, generate the app using shell commands:

**2.1 Create app directory structure:**
```bash
# Copy template to new app directory
cp -r ~/.claude/skills/databricks-deep-agent-app/assets/app-template ./APP_NAME
```

**2.2 Configure system prompt:**
```bash
# Write system prompt to agent/system_prompt.md
cat > ./APP_NAME/agent/system_prompt.md << 'EOF'
[SYSTEM_PROMPT_CONTENT]
EOF
```

**2.3 Update app.yaml with app name:**
```bash
# Replace placeholder in app.yaml
sed -i 's/{{APP_NAME}}/ACTUAL_APP_NAME/g' ./APP_NAME/app.yaml
```

**2.4 Copy skills (if requested):**
```bash
# For each skill the user wants to include:
cp -r /path/to/skill ./APP_NAME/agent/skills/
```

**2.5 Show user what was generated:**
```bash
# List the generated structure
ls -la ./APP_NAME/
```

### Step 3: Deploy to Databricks

Use AskUserQuestion to gather deployment information:
- Workspace email (e.g., user@company.com)
- Databricks CLI profile (default: DEFAULT)

Then deploy using databricks CLI commands:

**3.1 Verify authentication:**
```bash
databricks auth token --profile PROFILE
```

**3.2 Create app (if doesn't exist):**
```bash
databricks apps create APP_NAME --profile PROFILE
```

**3.3 Deploy the app:**
```bash
cd ./APP_NAME
databricks apps deploy APP_NAME --source-code-path . --profile PROFILE
```

**3.4 Get app status and URL:**
```bash
databricks apps get APP_NAME --profile PROFILE --output json | jq -r '.url'
```

### Step 4: Test the Deployment

Test the deployed app using curl:

```bash
# Get auth token
TOKEN=$(databricks auth token --profile PROFILE)

# Test health endpoint
curl -H "Authorization: Bearer $TOKEN" https://APP_URL/health

# Test chat completions
curl -X POST https://APP_URL/api/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Key Workflow Principles

1. **Ask first, generate later** - Always gather requirements using AskUserQuestion before generating anything
2. **Propose sensible defaults** - Suggest app names and system prompts based on the user's domain
3. **Show your work** - Display the commands you're running so users can verify
4. **Use shell commands** - Prefer cp, sed, cat, and databricks CLI over Python scripts
5. **Validate as you go** - Check that each step succeeds before proceeding

## Generated App Architecture

### Directory Structure

```
my-agent/
├── app.py                  # FastAPI application
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── app.yaml               # Databricks deployment config
├── .syncignore            # Deployment exclusions
├── .env.example           # Environment variable template
├── agent/
│   ├── __init__.py
│   ├── core.py            # Agent initialization
│   ├── provider.py        # Multi-provider support
│   ├── config.py          # Agent configuration
│   ├── system_prompt.md   # Your custom system prompt
│   └── skills/            # Your skills
│       └── skill-name/
│           ├── SKILL.md
│           └── references/
├── routes/
│   └── v1/
│       ├── completions.py # OpenAI-compatible endpoint
│       └── healthcheck.py # Health monitoring
└── models/
    └── openai_schema.py   # Pydantic models
```

### Key Features

**OpenAI-Compatible API:**
- POST `/api/v1/chat/completions`
- Accepts OpenAI message format
- Returns OpenAI response format
- Supports multi-turn conversations

**Multi-Provider Support:**
- Databricks (default: databricks-claude-sonnet-4-5)
- Anthropic (Claude models)
- OpenAI (GPT models)
- Azure OpenAI

**Configuration via Environment Variables:**
```bash
AGENT_PROVIDER=databricks
AGENT_MODEL=databricks-claude-sonnet-4-5
AGENT_AUTO_APPROVE=true
AGENT_WORKSPACE=/tmp/agent-workspace
```

**Automatic Authentication:**
- Databricks Apps provide DATABRICKS_HOST and DATABRICKS_TOKEN
- No manual token management required

## Additional Resources

- **Advanced Usage**: See [advanced_usage.md](references/advanced_usage.md)
  - Custom configuration (multi-provider setup, environment variables)
  - Adding skills after generation
  - Local testing before deployment

- **Troubleshooting**: See [troubleshooting.md](references/troubleshooting.md)
  - Authentication issues
  - Deployment issues
  - Skill validation errors

- **Best Practices**: See [best_practices.md](references/best_practices.md)
  - System prompt design guidelines
  - Skill organization
  - Deployment and security best practices
  - Cost optimization and performance tuning

- **Deployment Guide**: See [databricks_deployment.md](references/databricks_deployment.md)
  - Detailed deployment troubleshooting
  - Monitoring and logs
  - Multiple environments

- **Architecture Overview**: See [architecture.md](references/architecture.md)
  - Deep agent system details
  - Provider implementations
  - Configuration patterns

## Requirements

- **Python:** 3.11+
- **Databricks CLI:** Configured with valid profile
- **Databricks Workspace:** Access and permissions
- **Dependencies:** Automatically installed from requirements.txt
