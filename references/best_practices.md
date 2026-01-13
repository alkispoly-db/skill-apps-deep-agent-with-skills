# Best Practices

Guidelines and recommendations for building effective Databricks Deep Agent Apps.

## System Prompt Design

### Good Example
```
You are a SQL query optimizer for MySQL databases.
Help users write efficient queries by:
- Analyzing query plans
- Suggesting index optimizations
- Rewriting suboptimal queries
- Explaining performance bottlenecks
```

### Avoid
```
You are helpful.
```

### Guidelines
- Be specific about the domain and capabilities
- List concrete tasks the agent can perform
- Include any constraints or guidelines
- Mention expected output formats if relevant

## Skill Organization

- Keep skills focused and single-purpose
- Use descriptive skill names (e.g., "sql-optimizer" not "helper")
- Include reference materials in skills/references/
- Test skills individually before deploying
- Document skill dependencies in SKILL.md

## Deployment Best Practices

- Test locally first with `uvicorn app:app --reload`
- Use meaningful app names (e.g., "sql-assistant" not "test-app-1")
- Keep apps updated with regular redeployments
- Monitor logs after deployment
- Use separate apps for dev/staging/prod
- Document environment-specific configurations

## Cost Optimization

- Choose appropriate models for task complexity
- Use smaller models for simple tasks
- Stop apps when not in use: `databricks apps stop <app-name>`
- Monitor usage via Databricks workspace
- Set appropriate timeout values
- Consider caching strategies for repeated queries

## Security Considerations

- Never hardcode API keys in app.yaml
- Use Databricks secrets for sensitive values
- Limit workspace permissions appropriately
- Regularly rotate authentication tokens
- Review app logs for suspicious activity

## Performance Tuning

- Monitor response times via logs
- Optimize system prompts to be concise
- Reduce number of skills if not needed
- Use appropriate model sizes
- Consider implementing caching
