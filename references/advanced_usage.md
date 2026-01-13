# Advanced Usage Guide

This guide covers advanced scenarios, troubleshooting, and best practices for the Databricks Deep Agent App Generator.

## Table of Contents

- [Custom Configuration](#custom-configuration)
- [Adding Skills After Generation](#adding-skills-after-generation)
- [Local Testing Before Deployment](#local-testing-before-deployment)
- [Troubleshooting](#troubleshooting)
- [Tips and Best Practices](#tips-and-best-practices)

## Custom Configuration

Edit `app.yaml` in generated app to customize provider and model settings:

```yaml
env:
  - name: AGENT_PROVIDER
    value: "anthropic"
  - name: AGENT_MODEL
    value: "claude-sonnet-4-5"
  - name: ANTHROPIC_API_KEY
    value: "your-api-key"  # Or use secrets
```

Available providers:
- `databricks` (default) - Uses Databricks Foundation Model API
- `anthropic` - Direct Claude API access
- `openai` - OpenAI GPT models
- `azure` - Azure OpenAI

## Adding Skills After Generation

Copy additional skills to the app after initial generation:

```bash
# Copy additional skills to the app
cp -r ~/my-skills/new-skill ./my-agent/agent/skills/
```

Then redeploy:
```bash
cd ./my-agent
databricks apps deploy APP_NAME --source-code-path . --profile DEFAULT
```

## Local Testing Before Deployment

Test your app locally before deploying to Databricks:

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

For more troubleshooting, see [databricks_deployment.md](databricks_deployment.md).

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

**Guidelines:**
- Be specific about the domain and capabilities
- List concrete tasks the agent can perform
- Include any constraints or guidelines
- Mention expected output formats if relevant

### Skill Organization

- Keep skills focused and single-purpose
- Use descriptive skill names (e.g., "sql-optimizer" not "helper")
- Include reference materials in skills/references/
- Test skills individually before deploying
- Document skill dependencies in SKILL.md

### Deployment Best Practices

- Test locally first with `uvicorn app:app --reload`
- Use meaningful app names (e.g., "sql-assistant" not "test-app-1")
- Keep apps updated with regular redeployments
- Monitor logs after deployment
- Use separate apps for dev/staging/prod
- Document environment-specific configurations

### Cost Optimization

- Choose appropriate models for task complexity
- Use smaller models for simple tasks
- Stop apps when not in use: `databricks apps stop <app-name>`
- Monitor usage via Databricks workspace
- Set appropriate timeout values
- Consider caching strategies for repeated queries

### Security Considerations

- Never hardcode API keys in app.yaml
- Use Databricks secrets for sensitive values
- Limit workspace permissions appropriately
- Regularly rotate authentication tokens
- Review app logs for suspicious activity

### Performance Tuning

- Monitor response times via logs
- Optimize system prompts to be concise
- Reduce number of skills if not needed
- Use appropriate model sizes
- Consider implementing caching
