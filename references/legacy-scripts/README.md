# Legacy Scripts

These Python scripts were part of the original skill design but have been replaced by an interactive, shell-based workflow.

They are kept here for reference only and should not be used in the primary workflow.

## Files

- `generate_app.py` - Original app generation script (replaced by interactive workflow)
- `deploy_app.py` - Original deployment script (replaced by databricks CLI commands)
- `test_app.py` - Original testing script (replaced by curl commands)

## Why These Were Replaced

The skill now follows an interactive approach where:
1. Gather requirements using AskUserQuestion
2. Use shell commands directly (cp, sed, cat, databricks CLI)
3. Show users each step transparently so they can verify

This makes the workflow more transparent and easier to customize.
