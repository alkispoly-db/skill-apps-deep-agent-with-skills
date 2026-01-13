#!/usr/bin/env python3
"""
Generate a customized Databricks deep agent app from template.

This script creates a new app directory with:
- Customized system prompt
- Selected or created skills
- Complete FastAPI application structure
- Deployment configuration
"""
import argparse
import shutil
from pathlib import Path
from typing import List, Optional
import sys


def copy_template(template_dir: Path, output_dir: Path, app_name: str) -> Path:
    """
    Copy template and create app directory.

    Args:
        template_dir: Path to app-template directory
        output_dir: Output directory for new app
        app_name: Name of the app

    Returns:
        Path to created app directory
    """
    app_dir = output_dir / app_name

    if app_dir.exists():
        print(f"Error: Directory {app_dir} already exists")
        sys.exit(1)

    print(f"Creating app directory: {app_dir}")
    shutil.copytree(template_dir, app_dir)

    return app_dir


def get_system_prompt(prompt_or_path: str) -> str:
    """
    Load system prompt from text or file.

    Args:
        prompt_or_path: Either inline text or path to .md file

    Returns:
        System prompt content
    """
    # Check if it's a file path
    path = Path(prompt_or_path)
    if path.exists() and path.is_file():
        print(f"Loading system prompt from: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content.strip()

    # Otherwise treat as inline text
    print("Using inline system prompt")
    return prompt_or_path.strip()


def replace_placeholders(app_dir: Path, app_name: str, system_prompt: str) -> None:
    """
    Replace placeholders in template files.

    Args:
        app_dir: App directory path
        app_name: Name of the app
        system_prompt: System prompt content
    """
    # Replace system prompt
    system_prompt_file = app_dir / "agent" / "system_prompt.md"
    print(f"Writing system prompt to: {system_prompt_file}")
    with open(system_prompt_file, 'w', encoding='utf-8') as f:
        f.write(system_prompt)

    # Replace app name in app.yaml
    app_yaml = app_dir / "app.yaml"
    if app_yaml.exists():
        print(f"Updating app name in: {app_yaml}")
        with open(app_yaml, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace("{{APP_NAME}}", app_name)

        with open(app_yaml, 'w', encoding='utf-8') as f:
            f.write(content)


def validate_skill_directory(skill_path: Path) -> bool:
    """
    Validate that a directory is a valid skill.

    Args:
        skill_path: Path to skill directory

    Returns:
        True if valid skill, False otherwise
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"Error: {skill_path} is missing SKILL.md")
        return False

    # Check for frontmatter
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip().startswith('---'):
        print(f"Error: {skill_md} is missing YAML frontmatter")
        return False

    return True


def copy_skill(skill_path: Path, dest_dir: Path) -> None:
    """
    Copy an existing skill directory.

    Args:
        skill_path: Path to source skill
        dest_dir: Destination skills directory
    """
    if not validate_skill_directory(skill_path):
        sys.exit(1)

    skill_name = skill_path.name
    dest_path = dest_dir / skill_name

    if dest_path.exists():
        print(f"Warning: Skill {skill_name} already exists in destination, skipping")
        return

    print(f"Copying skill: {skill_name}")
    shutil.copytree(skill_path, dest_path)
    print(f"✓ Skill copied to: {dest_path}")


def create_new_skill(dest_dir: Path) -> None:
    """
    Guide user through creating a new skill.

    Args:
        dest_dir: Destination skills directory
    """
    print("\n=== Create New Skill ===")
    skill_name = input("Skill name (e.g., 'sql-optimizer'): ").strip()

    if not skill_name:
        print("Error: Skill name cannot be empty")
        return

    skill_dir = dest_dir / skill_name
    if skill_dir.exists():
        print(f"Error: Skill {skill_name} already exists")
        return

    skill_dir.mkdir(parents=True, exist_ok=True)

    # Get skill description
    print("Enter skill description (what it does, when to use it):")
    description = input("> ").strip()

    # Create basic SKILL.md
    skill_md = skill_dir / "SKILL.md"
    content = f"""---
name: {skill_name}
description: {description}
---

# {skill_name}

## Usage

[Add usage instructions here]

## Examples

[Add examples here]
"""

    with open(skill_md, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Created new skill: {skill_name}")
    print(f"  Edit SKILL.md to add full instructions: {skill_md}")


def handle_skills_workflow(app_dir: Path) -> None:
    """
    Interactive skill selection: copy existing or create new.

    Args:
        app_dir: App directory path
    """
    skills_dir = app_dir / "agent" / "skills"

    print("\n=== Skills Configuration ===")

    while True:
        print("\nOptions:")
        print("  1. Copy existing skill")
        print("  2. Create new skill")
        print("  3. Done")

        choice = input("\nChoose option (1-3): ").strip()

        if choice == "1":
            skill_path = input("Enter path to skill directory: ").strip()
            path = Path(skill_path).expanduser().resolve()

            if not path.exists():
                print(f"Error: Path does not exist: {path}")
                continue

            if not path.is_dir():
                print(f"Error: Path is not a directory: {path}")
                continue

            copy_skill(path, skills_dir)

        elif choice == "2":
            create_new_skill(skills_dir)

        elif choice == "3":
            break

        else:
            print("Invalid choice, please enter 1, 2, or 3")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a customized Databricks deep agent app"
    )
    parser.add_argument(
        "app_name",
        help="Name for your app (e.g., 'sql-assistant', 'marketing-agent')"
    )
    parser.add_argument(
        "--system-prompt",
        required=True,
        help="System prompt text OR path to .md file"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Where to create the app directory (default: current directory)"
    )
    parser.add_argument(
        "--no-skills",
        action="store_true",
        help="Skip skills configuration (create app without skills)"
    )

    args = parser.parse_args()

    # Get paths
    script_dir = Path(__file__).parent
    skill_dir = script_dir.parent
    template_dir = skill_dir / "assets" / "app-template"
    output_dir = Path(args.output_dir).resolve()

    # Validate template exists
    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}")
        sys.exit(1)

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Generating Databricks Deep Agent App")
    print(f"{'='*60}")
    print(f"App name: {args.app_name}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")

    # Copy template
    app_dir = copy_template(template_dir, output_dir, args.app_name)

    # Get system prompt
    system_prompt = get_system_prompt(args.system_prompt)

    # Replace placeholders
    replace_placeholders(app_dir, args.app_name, system_prompt)

    # Handle skills
    if not args.no_skills:
        add_skills = input("\nDo you want to include skills? [y/n]: ").strip().lower()
        if add_skills == 'y':
            handle_skills_workflow(app_dir)

    print(f"\n{'='*60}")
    print(f"✓ App created successfully!")
    print(f"{'='*60}")
    print(f"Location: {app_dir}")
    print(f"\nNext steps:")
    print(f"  1. Review the generated app")
    print(f"  2. Deploy to Databricks:")
    print(f"     python scripts/deploy_app.py {app_dir}")
    print(f"  3. Test deployment:")
    print(f"     python scripts/test_app.py <APP_URL>")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
