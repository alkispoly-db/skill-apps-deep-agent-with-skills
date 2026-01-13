# Deploying to Databricks Apps

Quick guide for deploying the Marketing Research Agent to Databricks Apps.

## Quick Start

**Prerequisites**: Databricks CLI configured with a profile (assumes `~/.databrickscfg` is already set up)

### 1. Create the App

```bash
databricks apps create skill-agent \
  --description "Marketing Research Agent with Deep Agent System" \
  --profile DEFAULT
```

### 2. Upload Source Code

```bash
# Sync code to workspace (excludes .venv, .git, etc.)
databricks sync --exclude-from .syncignore . \
  /Workspace/Users/YOUR.EMAIL@company.com/apps/skill-agent
```

**Note**: The `.syncignore` file excludes `.venv`, `.git`, `__pycache__`, and other unnecessary files from upload.

### 3. Deploy

```bash
databricks apps deploy skill-agent \
  --source-code-path /Workspace/Users/YOUR.EMAIL@company.com/apps/skill-agent
```

### 4. Get Your App URL

```bash
databricks apps get skill-agent --output json | jq -r '.url'
```

### 5. Test with chat_cli.py

```bash
python chat_cli.py \
  --url https://your-app-id.databricksapps.com \
  --databricks-profile DEFAULT
```

---

## Configuration

### app.yaml (Already Configured)

The project includes a pre-configured `app.yaml`:

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

**Key Points**:
- Port 8000 is required by Databricks Apps
- Environment variables configure the agent to use Databricks Foundation Model API
- `DATABRICKS_HOST` and `DATABRICKS_TOKEN` are automatically provided by the platform

### .databricksignore (Already Configured)

The project includes a `.databricksignore` file that excludes:
- `.venv/` and `venv/` - Virtual environments
- `__pycache__/` and `*.pyc` - Python cache files
- `.git/` - Git repository data
- `chat_cli.py` - Local testing script
- Documentation files - `README.md`, `DATABRICKS_DEPLOYMENT.md`, etc.

---

## Monitoring

### View Logs

```bash
# Tail logs in real-time
databricks apps logs skill-agent --follow

# View recent logs
databricks apps logs skill-agent --tail 50
```

### Check Status

```bash
# Get app status
databricks apps get skill-agent

# List all apps
databricks apps list
```

---

## Testing Your Deployed App

### Option 1: Using chat_cli.py (Recommended)

The `chat_cli.py` script supports Databricks authentication:

```bash
# Connect using your Databricks profile
python chat_cli.py \
  --url https://skill-agent-YOUR-ID.databricksapps.com \
  --databricks-profile DEFAULT

# Or use a different profile
python chat_cli.py \
  --url https://your-app.databricksapps.com \
  --databricks-profile production
```

**Features**:
- Automatic authentication using your Databricks CLI configuration
- Interactive chat with conversation history
- Type `clear` to reset conversation
- Type `quit` or `exit` to end session

### Option 2: Using curl

```bash
# Get your Databricks token
TOKEN=$(databricks auth token)

# Test health check
curl -H "Authorization: Bearer $TOKEN" \
  https://your-app.databricksapps.com/api/v1/healthcheck

# Test chat endpoint
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Suggest a cookie flavor"}]}' \
  https://your-app.databricksapps.com/api/v1/chat/completions
```

### Option 3: Through Databricks UI

1. Go to your Databricks workspace
2. Click **Apps** in the left sidebar
3. Find **skill-agent** in the list
4. Click **"Open App"**
5. Access the API docs at `/docs`

---

## Updating Your App

### Update Code

```bash
# Make changes to your code locally

# Sync updated files
databricks sync --exclude-from .syncignore . \
  /Workspace/Users/YOUR.EMAIL@company.com/apps/skill-agent

# Redeploy (this will automatically restart the app)
databricks apps deploy skill-agent \
  --source-code-path /Workspace/Users/YOUR.EMAIL@company.com/apps/skill-agent
```

### Manual Stop/Start

```bash
# Stop the app
databricks apps stop skill-agent

# Start the app (triggers redeployment)
databricks apps start skill-agent
```

---

## Common Commands Reference

```bash
# Create app
databricks apps create <app-name> --description "Description"

# Deploy app
databricks apps deploy <app-name> --source-code-path /Workspace/path/to/code

# Get app info
databricks apps get <app-name>

# View logs
databricks apps logs <app-name> --follow

# Restart app
databricks apps restart <app-name>

# Delete app
databricks apps delete <app-name>

# List all apps
databricks apps list

# Get app URL
databricks apps get <app-name> --output json | jq -r '.url'
```

---

## Deployment Architecture

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
│   │   └── cookie-flavor-generator
│   └── System Prompt (agent/system_prompt.md)
│
└── API Endpoints
    ├── / (root with API info)
    ├── /docs (interactive API docs)
    ├── /api/v1/healthcheck
    └── /api/v1/chat/completions
```

---

## Troubleshooting

### App Won't Start

**Check logs:**
```bash
databricks apps logs skill-agent
```

**Common issues:**
- Missing dependencies in `requirements.txt`
- Incorrect port (must be 8000)
- Syntax errors in code
- Missing required files

### Authentication Errors

**Issue**: 401 Unauthorized when testing

**Solution**:
```bash
# Verify your authentication works
databricks auth token

# Use chat_cli.py with profile
python chat_cli.py --url <URL> --databricks-profile DEFAULT
```

### Model Access Errors

**Issue**: 404 error when accessing models

**Check available models:**
```bash
databricks serving-endpoints list
```

**Verify model name** in `app.yaml`:
- Default: `databricks-claude-sonnet-4-5`
- Available models accessible through Foundation Model API

### Connection Issues with chat_cli.py

**Error**: "Could not connect"

**Verify**:
1. App is running: `databricks apps get skill-agent`
2. URL is correct: `databricks apps get skill-agent --output json | jq -r '.url'`
3. Profile authentication works: `databricks auth token --profile DEFAULT`

### Deployment Fails

**Error**: "App with name X does not exist"

**Solution**: Create the app first:
```bash
databricks apps create skill-agent --description "Marketing Research Agent"
```

---

## Multiple Environments

Deploy to different environments using profiles:

```bash
# Staging
databricks apps create skill-agent-staging \
  --profile staging

databricks apps deploy skill-agent-staging \
  --source-code-path /Workspace/.../skill-agent \
  --profile staging

# Production
databricks apps create skill-agent-prod \
  --profile production

databricks apps deploy skill-agent-prod \
  --source-code-path /Workspace/.../skill-agent \
  --profile production
```

---

## Cost Optimization

### Resource Management

Monitor your app's resource usage:
```bash
databricks apps get skill-agent --output json | jq '{compute_size, app_status}'
```

### Idle Apps

Stop apps when not in use:
```bash
databricks apps stop skill-agent
```

Restart when needed:
```bash
databricks apps start skill-agent
```

---

## Security Best Practices

1. **Use Service Principals** for production deployments
2. **Rotate tokens** regularly (handled automatically by Databricks Apps)
3. **Limit permissions** to only what the app needs
4. **Review logs** regularly for unauthorized access attempts
5. **Use separate environments** (dev/staging/prod) with different profiles

---

## Additional Resources

- [Databricks Apps Documentation](https://docs.databricks.com/dev-tools/databricks-apps/)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/)
- [Foundation Model APIs](https://docs.databricks.com/machine-learning/foundation-models/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)

---

## Need Help?

1. **Check logs**: `databricks apps logs skill-agent`
2. **Verify status**: `databricks apps get skill-agent`
3. **Test locally** first with: `uvicorn app:app --host 0.0.0.0 --port 8000`
4. **Contact** Databricks support or your workspace admin
