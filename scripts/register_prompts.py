"""Register agent prompts as versioned entries in LangFuse Prompt Management.

Reads the current prompt constants from each agent module and uploads them
to LangFuse as text prompts. Supports version tagging for A/B comparison.

Usage:
  python scripts/register_prompts.py              # Register as v3
  python scripts/register_prompts.py --version v4 # Register as v4
  python scripts/register_prompts.py --list        # List registered prompts
  python scripts/register_prompts.py --diff        # Compare code vs LangFuse

Requires:
  LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY in local/.env
"""

import argparse
import ast
import difflib
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / "local" / ".env")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = PROJECT_ROOT / "services" / "ai_service" / "app" / "agent"
GUARDRAILS_DIR = PROJECT_ROOT / "services" / "ai_service" / "app"

# Source file -> (variable name, LangFuse prompt name, labels)
PROMPT_SOURCES = [
    ("learning_advisor.py", "ADVISOR_PROMPT", "learning-advisor", ["orchestrator", "routing"]),
    ("skill_gap.py", "SKILL_GAP_PROMPT", "skill-gap-analyst", ["specialist", "skill-gap"]),
    ("career.py", "CAREER_PROMPT", "career-advisor", ["specialist", "career"]),
    ("learning_path.py", "LEARNING_PATH_PROMPT", "learning-path-designer", ["specialist", "learning-path"]),
]

# Guardrail prompts — LLM-as-Judge, must be version-managed
GUARDRAIL_PROMPT_SOURCES = [
    ("guardrails.py", "TOPIC_CLASSIFIER_PROMPT", "topic-classifier", ["guardrail", "llm-as-judge"]),
]


def _extract_prompt(file_path: Path, var_name: str) -> str:
    """Extract a string constant from a Python file using AST (no import needed)."""
    tree = ast.parse(file_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    return ast.literal_eval(node.value)
    raise ValueError(f"Could not find {var_name} in {file_path}")


def _load_prompts() -> dict:
    """Load all prompt texts from source files via AST parsing."""
    prompts = {}
    for filename, var_name, prompt_name, labels in PROMPT_SOURCES:
        file_path = AGENT_DIR / filename
        text = _extract_prompt(file_path, var_name)
        prompts[prompt_name] = {"prompt": text, "labels": labels}
        logger.info("Loaded: %s (%d chars)", prompt_name, len(text))
    for filename, var_name, prompt_name, labels in GUARDRAIL_PROMPT_SOURCES:
        file_path = GUARDRAILS_DIR / filename
        text = _extract_prompt(file_path, var_name)
        prompts[prompt_name] = {"prompt": text, "labels": labels}
        logger.info("Loaded: %s (%d chars)", prompt_name, len(text))
    return prompts


PROMPTS = _load_prompts()


def _get_client():
    """Get LangFuse client."""
    import os

    from langfuse import Langfuse

    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com"),
    )


def register_prompts(version: str) -> None:
    """Register all agent prompts in LangFuse with the given version label."""
    client = _get_client()

    if not client.auth_check():
        logger.error("LangFuse auth failed. Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY.")
        sys.exit(1)

    for name, config in PROMPTS.items():
        try:
            client.create_prompt(
                name=name,
                prompt=config["prompt"],
                labels=[version] + config["labels"],
                type="text",
            )
            logger.info("Registered: %s (%s)", name, version)
        except Exception as e:
            # LangFuse auto-increments version numbers internally;
            # labels are used for our logical version tracking (v1, v2, etc.)
            logger.error("Failed to register %s: %s", name, e)

    client.flush()
    logger.info("Done. All prompts registered with label '%s'.", version)


def list_prompts(label: str | None = None) -> None:
    """List all registered prompts and their versions."""
    client = _get_client()

    if not client.auth_check():
        logger.error("LangFuse auth failed.")
        sys.exit(1)

    for name in PROMPTS:
        try:
            # Fetch specific label or latest version
            if label:
                prompt = client.get_prompt(name, label=label)
            else:
                prompt = client.get_prompt(name, label="latest")
            logger.info(
                "%s: version=%s, labels=%s",
                prompt.name,
                prompt.version,
                prompt.labels,
            )
        except Exception:
            logger.info("%s: not registered yet", name)


def diff_prompts() -> None:
    """Compare code prompts with the latest versions in LangFuse."""
    client = _get_client()

    if not client.auth_check():
        logger.error("LangFuse auth failed.")
        sys.exit(1)

    has_diff = False
    for name, config in PROMPTS.items():
        try:
            remote = client.get_prompt(name, label="latest")
            remote_text = remote.prompt
        except Exception:
            logger.info("[%s] not in LangFuse yet (will be created on register)", name)
            has_diff = True
            continue

        local_text = config["prompt"]
        if local_text.strip() == remote_text.strip():
            logger.info("[%s] in sync (LangFuse v%s)", name, remote.version)
        else:
            has_diff = True
            logger.info("[%s] DIFFERS from LangFuse v%s:", name, remote.version)
            diff = difflib.unified_diff(
                remote_text.splitlines(keepends=True),
                local_text.splitlines(keepends=True),
                fromfile=f"langfuse (v{remote.version})",
                tofile="code (local)",
            )
            sys.stdout.writelines(diff)
            print()

    if not has_diff:
        logger.info("\nAll prompts are in sync with LangFuse.")
    else:
        logger.info("\nRun with --version <tag> to register updated prompts.")


def main():
    parser = argparse.ArgumentParser(description="Register agent prompts in LangFuse")
    parser.add_argument(
        "--version",
        default="v3",
        help="Version label for the prompts (default: v3)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List registered prompts instead of registering",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Compare code prompts with LangFuse versions",
    )
    args = parser.parse_args()

    if args.list:
        list_prompts()
    elif args.diff:
        diff_prompts()
    else:
        register_prompts(args.version)


if __name__ == "__main__":
    main()
