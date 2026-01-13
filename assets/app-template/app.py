"""
Main FastAPI application for OpenAI-compatible chat completions API.

This application provides a Databricks-compatible FastAPI service that exposes
an OpenAI-compatible chat completions endpoint powered by a deep agent.
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from agent import create_agent
from routes.v1 import completions, healthcheck

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown.

    Initializes the agent at startup and ensures cleanup on shutdown.
    """
    # Startup: Initialize agent
    logger.info("=" * 60)
    logger.info("Initializing Marketing Research Agent")
    logger.info("=" * 60)
    logger.info(f"Provider: {config.agent_provider}")
    logger.info(f"Model: {config.agent_model}")
    logger.info(f"Workspace: {config.agent_workspace}")
    logger.info(f"Auto-approve: {config.agent_auto_approve}")

    # Configure Databricks authentication if using Databricks provider
    config.configure_databricks_environment()
    if config.agent_provider == "databricks":
        profile_msg = f"profile: {config.databricks_profile}" if config.databricks_profile else "profile: DEFAULT"
        logger.info(f"Using Databricks CLI authentication ({profile_msg})")
        if config.databricks_host:
            logger.info(f"Databricks host: {config.databricks_host}")

    try:
        agent = create_agent(
            provider=config.agent_provider,
            model_name=config.agent_model,
            endpoint=config.agent_endpoint,
            workspace_dir=config.agent_workspace,
            auto_approve=config.agent_auto_approve,
        )

        # Store agent in application state
        app.state.agent = agent

        logger.info("Agent initialized successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        raise RuntimeError(f"Agent initialization failed: {e}") from e

    # Application is running
    yield

    # Shutdown: Cleanup (if needed)
    logger.info("Shutting down agent...")

app = FastAPI(
    title="Databricks OpenAI-Compatible API",
    description="OpenAI-compatible chat completions endpoint powered by deep agent",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration - allow all origins for development
# Restrict in production as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api/v1 prefix (required for Databricks OAuth2)
app.include_router(healthcheck.router, prefix="/api/v1", tags=["health"])
app.include_router(completions.router, prefix="/api/v1", tags=["completions"])


@app.get("/")
async def root():
    """
    Root endpoint providing basic API information.

    Returns:
        dict: API status and available endpoints
    """
    return {
        "message": "OpenAI-Compatible API Server",
        "status": "running",
        "agent": {
            "provider": config.agent_provider,
            "model": config.agent_model,
        },
        "docs": "/docs",
        "healthcheck": "/api/v1/healthcheck",
        "completions": "/api/v1/chat/completions",
    }
