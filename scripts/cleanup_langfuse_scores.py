"""Delete old non-metric scores from LangFuse that distort the Score graph.

Removes scores with names like latency_ms, courses_count, etc. that were
previously uploaded as scores but should have been metadata.

Usage (from project root):
    python scripts/cleanup_langfuse_scores.py
    python scripts/cleanup_langfuse_scores.py --dry-run
"""

import argparse
import os
import sys
import time
from base64 import b64encode
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv

load_dotenv("local/.env")

# Score names that should never have been scores (they are operational metrics).
# latency_ms distorts the Y-axis (values 1000-20000+); courses_count is not a metric.
# advisor_tool_count and retrieval_tool_count are kept (values 0-2, harmless).
SCORES_TO_DELETE = {
    "latency_ms",
    "courses_count",
}


def main():  # noqa: C901
    """CLI entry point for cleaning up LangFuse scores."""
    parser = argparse.ArgumentParser(description="Clean up old LangFuse scores")
    parser.add_argument(
        "--dry-run", action="store_true", help="List scores without deleting"
    )
    args = parser.parse_args()

    from langfuse import Langfuse

    client = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com"),
    )

    if not client.auth_check():
        print("ERROR: LangFuse auth failed")
        sys.exit(1)

    # REST API client for delete (SDK lacks delete method)
    host = os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    auth = b64encode(f"{public_key}:{secret_key}".encode()).decode()
    http = httpx.Client(
        base_url=host,
        headers={"Authorization": f"Basic {auth}"},
        timeout=30.0,
    )

    total_deleted = 0

    for score_name in SCORES_TO_DELETE:
        print(f"\nSearching for scores named '{score_name}'...")
        page = 1

        while True:
            scores = client.api.scores.get_many(name=score_name, page=page, limit=100)

            if not scores.data:
                break

            print(f"  Found {len(scores.data)} scores (page {page})")

            if not args.dry_run:
                for score in scores.data:
                    for attempt in range(5):
                        try:
                            resp = http.delete(f"/api/public/scores/{score.id}")
                        except httpx.ReadTimeout:
                            print(f"    Timeout on {score.id}, retrying...")
                            time.sleep(2**attempt)
                            continue
                        if resp.status_code == 429:
                            wait = int(resp.headers.get("retry-after", 2**attempt))
                            print(f"    Rate limited, waiting {wait}s...")
                            time.sleep(wait)
                            continue
                        if resp.status_code < 300:
                            total_deleted += 1
                        else:
                            print(
                                f"    Failed to delete {score.id}: {resp.status_code}"
                            )
                        break
                    time.sleep(0.2)  # throttle requests
            else:
                for score in scores.data:
                    print(
                        f"    [dry-run] Would delete: id={score.id}, value={score.value}"
                    )
                total_deleted += len(scores.data)

            if not args.dry_run:
                # Re-fetch same page (items shift after deletion)
                continue
            if (
                not scores.meta
                or not scores.meta.total_pages
                or page >= scores.meta.total_pages
            ):
                break
            page += 1

    action = "Would delete" if args.dry_run else "Deleted"
    print(f"\n{action} {total_deleted} scores total.")

    if not args.dry_run and total_deleted > 0:
        print("Score graph should now show only 0-1 evaluation metrics.")


if __name__ == "__main__":
    main()
