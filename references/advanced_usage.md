# Advanced Usage

Advanced configuration and customization options for Databricks Deep Agent Apps.

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

### Available Providers

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
