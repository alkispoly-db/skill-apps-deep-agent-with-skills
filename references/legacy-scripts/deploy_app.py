#!/usr/bin/env python3
"""
Automate Databricks app deployment.

This script:
1. Validates Databricks CLI authentication
2. Creates Databricks app
3. Syncs code to workspace
4. Deploys app
5. Monitors deployment status
6. Returns app URL
"""
import argparse
import json
import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Optional


def run_command(cmd: list, capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command.

    Args:
        cmd: Command and arguments as list
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit

    Returns:
        CompletedProcess object
    """
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=check
    )
    return result


def check_databricks_auth(profile: str) -> bool:
    """
    Verify Databricks CLI is configured.

    Args:
        profile: Databricks CLI profile name

    Returns:
        True if authenticated, False otherwise
    """
    print(f"Checking Databricks authentication (profile: {profile})...")

    try:
        result = run_command(
            ["databricks", "auth", "token", "--profile", profile],
            capture_output=True,
            check=True
        )
        print("✓ Authentication successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Authentication failed: {e}")
        print("\nPlease configure Databricks CLI:")
        print(f"  databricks configure --token --profile {profile}")
        return False


def get_app_name_from_yaml(app_dir: Path) -> Optional[str]:
    """
    Extract app name from app.yaml description.

    Args:
        app_dir: App directory path

    Returns:
        App name or None
    """
    app_yaml = app_dir / "app.yaml"
    if not app_yaml.exists():
        return None

    with open(app_yaml, 'r') as f:
        # app.yaml doesn't have app name, we'll derive from directory
        pass

    return app_dir.name


def app_exists(app_name: str, profile: str) -> bool:
    """
    Check if Databricks app already exists.

    Args:
        app_name: App name
        profile: Databricks profile

    Returns:
        True if exists, False otherwise
    """
    try:
        result = run_command(
            ["databricks", "apps", "get", app_name, "--profile", profile],
            capture_output=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def create_databricks_app(app_name: str, description: str, profile: str) -> None:
    """
    Create Databricks app.

    Args:
        app_name: App name
        description: App description
        profile: Databricks profile
    """
    if app_exists(app_name, profile):
        print(f"✓ App {app_name} already exists, skipping creation")
        return

    print(f"Creating Databricks app: {app_name}")

    try:
        run_command([
            "databricks", "apps", "create", app_name,
            "--description", description,
            "--profile", profile
        ])
        print(f"✓ Created app: {app_name}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create app: {e}")
        sys.exit(1)


def sync_code(app_dir: Path, workspace_path: str, profile: str) -> None:
    """
    Sync code to workspace using databricks sync.

    Args:
        app_dir: Local app directory
        workspace_path: Workspace destination path
        profile: Databricks profile
    """
    print(f"Syncing code to workspace...")
    print(f"  Source: {app_dir}")
    print(f"  Destination: {workspace_path}")

    syncignore = app_dir / ".syncignore"
    if not syncignore.exists():
        print(f"Warning: .syncignore not found, all files will be synced")

    try:
        cmd = [
            "databricks", "sync",
            "--profile", profile,
            str(app_dir),
            workspace_path
        ]

        if syncignore.exists():
            cmd.insert(2, "--exclude-from")
            cmd.insert(3, str(syncignore))

        run_command(cmd)
        print("✓ Code synced successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to sync code: {e}")
        sys.exit(1)


def deploy_app(app_name: str, workspace_path: str, profile: str) -> None:
    """
    Deploy app to Databricks.

    Args:
        app_name: App name
        workspace_path: Workspace source code path
        profile: Databricks profile
    """
    print(f"Deploying app: {app_name}")

    try:
        run_command([
            "databricks", "apps", "deploy", app_name,
            "--source-code-path", workspace_path,
            "--profile", profile
        ])
        print("✓ Deployment started")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to deploy: {e}")
        sys.exit(1)


def get_app_status(app_name: str, profile: str) -> dict:
    """
    Get app status.

    Args:
        app_name: App name
        profile: Databricks profile

    Returns:
        App status dict
    """
    try:
        result = run_command([
            "databricks", "apps", "get", app_name,
            "--output", "json",
            "--profile", profile
        ])
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting app status: {e}")
        return {}


def wait_for_deployment(app_name: str, profile: str, timeout: int = 300) -> bool:
    """
    Monitor deployment until RUNNING or timeout.

    Args:
        app_name: App name
        profile: Databricks profile
        timeout: Timeout in seconds

    Returns:
        True if running, False on timeout
    """
    print(f"Monitoring deployment (timeout: {timeout}s)...")

    start_time = time.time()
    last_status = None

    while time.time() - start_time < timeout:
        status_info = get_app_status(app_name, profile)
        current_status = status_info.get("app_status", {}).get("state", "UNKNOWN")

        if current_status != last_status:
            print(f"  Status: {current_status}")
            last_status = current_status

        if current_status == "RUNNING":
            print("✓ App is RUNNING")
            return True

        if current_status in ["ERROR", "CRASHED"]:
            print(f"✗ Deployment failed with status: {current_status}")
            print("\nCheck logs:")
            print(f"  databricks apps logs {app_name} --profile {profile}")
            return False

        time.sleep(10)

    print(f"✗ Deployment timeout after {timeout}s")
    return False


def get_app_url(app_name: str, profile: str) -> Optional[str]:
    """
    Get app URL.

    Args:
        app_name: App name
        profile: Databricks profile

    Returns:
        App URL or None
    """
    status_info = get_app_status(app_name, profile)
    return status_info.get("url")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Databricks deep agent app"
    )
    parser.add_argument(
        "app_dir",
        help="Path to app directory"
    )
    parser.add_argument(
        "--app-name",
        help="Override app name (default: directory name)"
    )
    parser.add_argument(
        "--profile",
        default="DEFAULT",
        help="Databricks CLI profile (default: DEFAULT)"
    )
    parser.add_argument(
        "--workspace-email",
        help="Databricks workspace email (e.g., user@company.com)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Deployment timeout in seconds (default: 300)"
    )

    args = parser.parse_args()

    # Validate app directory
    app_dir = Path(args.app_dir).resolve()
    if not app_dir.exists():
        print(f"Error: App directory not found: {app_dir}")
        sys.exit(1)

    # Get app name
    app_name = args.app_name or app_dir.name

    # Get workspace email
    if not args.workspace_email:
        args.workspace_email = input("Enter your Databricks workspace email: ").strip()

    workspace_path = f"/Workspace/Users/{args.workspace_email}/apps/{app_name}"

    print(f"\n{'='*60}")
    print(f"Deploying Databricks Deep Agent App")
    print(f"{'='*60}")
    print(f"App name: {app_name}")
    print(f"App directory: {app_dir}")
    print(f"Workspace path: {workspace_path}")
    print(f"Profile: {args.profile}")
    print(f"{'='*60}\n")

    # Check authentication
    if not check_databricks_auth(args.profile):
        sys.exit(1)

    # Create app
    create_databricks_app(
        app_name,
        f"Deep agent app: {app_name}",
        args.profile
    )

    # Sync code
    sync_code(app_dir, workspace_path, args.profile)

    # Deploy
    deploy_app(app_name, workspace_path, args.profile)

    # Wait for deployment
    if wait_for_deployment(app_name, args.profile, args.timeout):
        app_url = get_app_url(app_name, args.profile)

        print(f"\n{'='*60}")
        print(f"✓ Deployment successful!")
        print(f"{'='*60}")
        print(f"App URL: {app_url}")
        print(f"\nNext steps:")
        print(f"  1. Test the app:")
        print(f"     python scripts/test_app.py {app_url} --profile {args.profile}")
        print(f"  2. View logs:")
        print(f"     databricks apps logs {app_name} --profile {args.profile}")
        print(f"{'='*60}\n")
    else:
        print("\n✗ Deployment failed or timed out")
        print(f"Check status: databricks apps get {app_name} --profile {args.profile}")
        print(f"View logs: databricks apps logs {app_name} --profile {args.profile}")
        sys.exit(1)


if __name__ == "__main__":
    main()
