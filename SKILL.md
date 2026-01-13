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

## System Prompt Templates

When proposing system prompts to users, use these domain-specific templates as starting points:

**Cooking/Recipe Agent:**
```
You are a culinary expert and recipe generation assistant. Help users create, modify, and understand cooking recipes.

Your capabilities include:
- Generating original recipes based on ingredients, cuisine type, dietary restrictions, or themes
- Adapting existing recipes for dietary needs (vegetarian, vegan, gluten-free, keto, etc.)
- Scaling recipes for different serving sizes
- Suggesting ingredient substitutions
- Providing cooking techniques and tips

When generating recipes, always include:
- Clear ingredient lists with measurements
- Step-by-step instructions
- Prep time, cook time, and total time
- Serving size
- Difficulty level
- Dietary information and allergen warnings
```

**SQL Assistant:**
```
You are a SQL expert who helps users write, optimize, and understand database queries.

Your capabilities include:
- Writing SQL queries for PostgreSQL/MySQL/other databases
- Optimizing slow queries and explaining query plans
- Designing database schemas and indexes
- Explaining complex SQL concepts
- Troubleshooting SQL errors

Always provide clear explanations and follow best practices for performance and security.
```

**Data Analysis Agent:**
```
You are a data analytics assistant specializing in exploratory data analysis and insights.

Your capabilities include:
- Analyzing datasets and identifying patterns
- Creating data visualizations
- Performing statistical analysis
- Deriving actionable insights from data
- Explaining analytical methodologies

Provide clear, data-driven recommendations with visualizations where appropriate.
```

Adapt these templates based on the user's specific domain and requirements.

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

## Advanced Usage

### Custom Configuration

Edit `app.yaml` in generated app:
```yaml
env:
  - name: AGENT_PROVIDER
    value: "anthropic"
  - name: AGENT_MODEL
    value: "claude-sonnet-4-5"
  - name: ANTHROPIC_API_KEY
    value: "your-api-key"  # Or use secrets
```

### Adding Skills After Generation

```bash
# Copy additional skills to the app
cp -r ~/my-skills/new-skill ./my-agent/agent/skills/
```

Then redeploy:
```bash
cd ./my-agent
databricks apps deploy APP_NAME --source-code-path . --profile DEFAULT
```

### Local Testing Before Deployment

```bash
cd my-agent

# Set environment variables
export AGENT_PROVIDER=databricks
export DATABRICKS_PROFILE=DEFAULT

# Start server
uvicorn app:app --reload --port 8000

# Test locally (in another terminal)
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

## Detailed References

For comprehensive information:

- **Deployment Guide**: See [databricks_deployment.md](references/databricks_deployment.md)
  - Troubleshooting deployment issues
  - Monitoring and logs
  - Multiple environments
  - Cost optimization

- **Architecture Overview**: See [architecture.md](references/architecture.md)
  - Deep agent system details
  - Provider implementations
  - Configuration patterns
  - Skill system internals

## Example Interactions

**Example 1: Cooking Recipe Agent**
```
User: "I want to create a databricks app that runs an agent to generate cooking recipes"

Follow the interactive workflow:
1. Use AskUserQuestion to propose app name "cooking-recipe-agent" and system prompt
2. Run: cp -r ~/.claude/skills/databricks-deep-agent-app/assets/app-template ./cooking-recipe-agent
3. Write system prompt using cat > ./cooking-recipe-agent/agent/system_prompt.md
4. Update app.yaml using sed
5. Show generated structure
6. Gather deployment info and deploy using databricks CLI
```

**Example 2: SQL Assistant with Skills**
```
User: "Build me a SQL assistant app with query optimization skills"

Follow the interactive workflow:
1. Propose app name "sql-assistant" and SQL-focused system prompt
2. Generate app structure
3. Ask if user has existing SQL skills to copy
4. Copy skills: cp -r ~/.claude/skills/sql-optimizer ./sql-assistant/agent/skills/
5. Deploy to Databricks
```

## Troubleshooting

### Issue: "Databricks authentication failed"

**Symptoms:**
```
✗ Authentication failed: ...
Please configure Databricks CLI:
  databricks configure --token --profile DEFAULT
```

**Solution:**
```bash
# Reconfigure Databricks CLI
databricks configure --token --profile DEFAULT

# Or verify existing configuration
databricks auth token --profile DEFAULT
```

### Issue: "Skill validation failed"

**Symptoms:**
```
Error: /path/to/skill is missing SKILL.md
# or
Error: /path/to/SKILL.md is missing YAML frontmatter
```

**Solution:**
Ensure SKILL.md has proper frontmatter:
```markdown
---
name: skill-name
description: Brief description
---

# Skill Content
```

### Issue: "Deployment timeout"

**Solution:**
```bash
# Check deployment logs
databricks apps logs APP_NAME --profile DEFAULT --follow

# Check app status
databricks apps get APP_NAME --profile DEFAULT
```

### Issue: "App returns errors after deployment"

**Solutions:**

1. **Check app logs:**
```bash
databricks apps logs APP_NAME --profile DEFAULT --follow
```

2. **Verify system prompt format:**
- Ensure system_prompt.md has valid content
- No unclosed placeholders

3. **Verify skills are valid:**
- Check each skill has SKILL.md with frontmatter
- Skills directory structure is correct

4. **Check environment variables:**
```bash
databricks apps get APP_NAME --output json | jq '.config.env'
```

### Issue: "Sync fails with authentication error"

**Symptoms:**
```
Error syncing code: authentication failed
```

**Solution:**
```bash
# Verify Databricks authentication
databricks auth token --profile DEFAULT

# Check workspace path permissions
databricks workspace ls /Workspace/Users/user@company.com/apps/

# Ensure email matches workspace user
databricks current-user --profile DEFAULT
```

For more troubleshooting, see [databricks_deployment.md](references/databricks_deployment.md).

## Requirements

- **Python:** 3.11+
- **Databricks CLI:** Configured with valid profile
- **Databricks Workspace:** Access and permissions
- **Dependencies:** Automatically installed from requirements.txt

## Notes

- Generated apps are self-contained and portable
- System prompts should be clear and specific
- Skills must have valid SKILL.md with frontmatter
- Deployment typically takes 1-2 minutes
- Apps auto-restart when code is updated
- Use .syncignore to exclude files from deployment
- Test locally before deploying to Databricks


## Tips and Best Practices

### System Prompt Design

**Good:**
```
You are a SQL query optimizer for MySQL databases.
Help users write efficient queries by:
- Analyzing query plans
- Suggesting index optimizations
- Rewriting suboptimal queries
- Explaining performance bottlenecks
```

**Avoid:**
```
You are helpful.
```

### Skill Organization

- Keep skills focused and single-purpose
- Use descriptive skill names (e.g., "sql-optimizer" not "helper")
- Include reference materials in skills/references/
- Test skills individually before deploying

### Deployment Best Practices

- Test locally first with `uvicorn app:app --reload`
- Use meaningful app names (e.g., "sql-assistant" not "test-app-1")
- Keep apps updated with regular redeployments
- Monitor logs after deployment
- Use separate apps for dev/staging/prod

### Cost Optimization

- Choose appropriate models for task complexity
- Use smaller models for simple tasks
- Stop apps when not in use: `databricks apps stop <app-name>`
- Monitor usage via Databricks workspace

## Additional Resources

For detailed information:
- **Deployment troubleshooting:** See [databricks_deployment.md](references/databricks_deployment.md)
- **Architecture details:** See [architecture.md](references/architecture.md)
