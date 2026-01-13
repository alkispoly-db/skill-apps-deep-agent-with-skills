# Troubleshooting Guide

Common issues and solutions when working with Databricks Deep Agent Apps.

## Authentication Issues

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

## Deployment Issues

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

## Skill Issues

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

## Additional Resources

For more detailed troubleshooting, see:
- [databricks_deployment.md](databricks_deployment.md) - Deployment-specific troubleshooting
- [architecture.md](architecture.md) - Understanding the system architecture
