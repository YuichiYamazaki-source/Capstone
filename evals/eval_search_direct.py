"""Direct search evaluation — bypasses LLM, calls hybrid_search() directly.

Isolates search quality from LLM parameter extraction non-determinism.
Each ground truth case is searched with a clean query string only.
No Learning Advisor, no prompt, no tool call extraction — pure retrieval.

Usage (inside Docker container):
    python -m evals.eval_search_direct
    python -m evals.eval_search_direct --limit 5
    python -m evals.eval_search_direct --show-all  # show full top-10 for each case
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv("local/.env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("eval.direct")

GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"


def load_ground_truth(limit: int | None = None) -> list[dict]:
    """Load ground truth test cases from JSON.

    Args:
        limit: Maximum number of test cases to return. None returns all.

    Returns:
        List of ground truth test case dictionaries.
    """
    with open(GROUND_TRUTH_PATH) as f:
        cases = json.load(f)
    if limit:
        cases = cases[:limit]
    return cases


async def main():
    """CLI entry point for direct search evaluation."""
    parser = argparse.ArgumentParser(description="Direct search evaluation (no LLM)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--show-all", action="store_true", help="Show all retrieved titles"
    )
    args = parser.parse_args()

    # Import after path setup so app modules resolve
    from app.clients.qdrant import get_qdrant_client
    from app.tools.hybrid_search import hybrid_search

    # Initialize Qdrant connection
    get_qdrant_client()

    cases = load_ground_truth(args.limit)
    logger.info("Running direct search for %d cases", len(cases))

    from evals.metrics import hit_rate, precision_at_k, recall_at_k

    total_hit = 0.0
    total_p5 = 0.0
    total_r5 = 0.0
    details = []

    for case in cases:
        query = case["query"]
        expected = case["expected_titles"]

        results = await hybrid_search(query=query, top_k=10)
        titles = [r.get("title", "") for r in results]

        hr = hit_rate(titles, expected)
        pk = precision_at_k(titles, expected, k=5)
        rk = recall_at_k(titles, expected, k=5)

        total_hit += hr
        total_p5 += pk
        total_r5 += rk

        detail = {
            "id": case["id"],
            "query": query,
            "hit_rate": hr,
            "precision_at_5": round(pk, 4),
            "recall_at_5": round(rk, 4),
            "top_5": titles[:5],
            "expected": expected,
        }

        # Check which expected titles appear anywhere in top 10
        titles_lower = {t.lower() for t in titles}
        found = [t for t in expected if t.lower() in titles_lower]
        missing = [t for t in expected if t.lower() not in titles_lower]
        detail["found_in_top10"] = found
        detail["missing"] = missing

        if args.show_all:
            detail["all_titles"] = titles

        details.append(detail)

        status = "HIT" if hr > 0 else "MISS"
        logger.info(
            "  [%s] %s: %s (p@5=%.2f, r@5=%.2f)", status, case["id"], query[:50], pk, rk
        )

    n = len(details) or 1
    summary = {
        "total_cases": len(details),
        "avg_hit_rate": round(total_hit / n, 4),
        "avg_precision_at_5": round(total_p5 / n, 4),
        "avg_recall_at_5": round(total_r5 / n, 4),
    }

    print("\n=== DIRECT SEARCH RESULTS ===")
    print(
        json.dumps(
            {"summary": summary, "details": details}, indent=2, ensure_ascii=False
        )
    )
    print("=== END ===")

    from app.clients.qdrant import close_qdrant_client

    close_qdrant_client()


if __name__ == "__main__":
    asyncio.run(main())
