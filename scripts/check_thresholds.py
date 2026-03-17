"""Check evaluation results against quality gate thresholds.

Usage:
    python scripts/check_thresholds.py [--results PATH] [--thresholds PATH]

Reads the most recent eval results JSON and compares each metric against
the defined thresholds. Exits with code 0 (pass) or 1 (fail).
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent.parent / "evals" / "results"
DEFAULT_THRESHOLDS = Path(__file__).resolve().parent.parent / "thresholds.yaml"


def load_latest_results(results_dir: Path) -> dict:
    """Load the most recent JSON results file from the results directory."""
    json_files = sorted(results_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not json_files:
        print(f"ERROR: No result files found in {results_dir}")
        sys.exit(1)
    latest = json_files[-1]
    print(f"Loading results: {latest.name}")
    with open(latest) as f:
        return json.load(f)


def load_thresholds(path: Path) -> dict:
    """Load threshold configuration from YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def check_metric(name: str, actual: float | None, threshold: float, op: str) -> bool:
    """Check a single metric against its threshold.

    Args:
        name: Metric display name.
        actual: Measured value (None if missing).
        threshold: Threshold value.
        op: Comparison operator ("gte" for >=, "lte" for <=).

    Returns:
        True if the metric passes.
    """
    if actual is None:
        print(f"  SKIP  {name}: not found in results")
        return True  # Don't fail on missing metrics

    if op == "gte":
        passed = actual >= threshold
        symbol = ">="
    else:
        passed = actual <= threshold
        symbol = "<="

    status = "PASS" if passed else "FAIL"
    print(f"  {status}  {name}: {actual:.3f} {symbol} {threshold:.3f}")
    return passed


def _check_section(
    section_name: str,
    thresholds_section: dict,
    results_section: dict,
    op: str,
) -> bool:
    """Check all metrics in a threshold section."""
    print(f"\n--- {section_name} ---")
    prefix = "max_" if op == "lte" else "min_"
    passed = True
    for key, threshold_val in thresholds_section.items():
        metric_name = key.replace(prefix, "")
        actual = results_section.get(metric_name)
        if not check_metric(metric_name, actual, threshold_val, op):
            passed = False
    return passed


def run_checks(results: dict, thresholds: dict) -> bool:
    """Run all threshold checks and return overall pass/fail."""
    # Define sections: (display_name, threshold_key, result_keys, operator)
    sections = [
        ("IR Metrics", "ir_metrics", ["ir_metrics", "search_metrics"], "gte"),
        ("Latency", "latency", ["latency"], "lte"),
        ("Guardrails", "guardrails", ["guardrails"], "gte"),
        ("Agent Routing", "agent_routing", ["agent_routing"], "gte"),
        ("Quality (DeepEval)", "quality", ["quality", "deepeval"], "gte"),
    ]

    all_passed = True
    for name, t_key, r_keys, op in sections:
        t_section = thresholds.get(t_key, {})
        # Try multiple result keys (fallback aliases)
        r_section: dict = {}
        for rk in r_keys:
            r_section = results.get(rk, {})
            if r_section:
                break
        if not _check_section(name, t_section, r_section, op):
            all_passed = False

    return all_passed


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Check eval results against thresholds")
    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Results directory or JSON file",
    )
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=DEFAULT_THRESHOLDS,
        help="Thresholds YAML file",
    )
    args = parser.parse_args()

    # Load results
    if args.results.is_dir():
        results = load_latest_results(args.results)
    else:
        with open(args.results) as f:
            results = json.load(f)

    thresholds = load_thresholds(args.thresholds)

    print("=" * 50)
    print("Quality Gate Check")
    print("=" * 50)

    passed = run_checks(results, thresholds)

    print("\n" + "=" * 50)
    if passed:
        print("RESULT: ALL GATES PASSED")
        sys.exit(0)
    else:
        print("RESULT: SOME GATES FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
