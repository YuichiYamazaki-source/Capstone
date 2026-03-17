#!/usr/bin/env bash
# CI pipeline runner: tests + threshold checks.
#
# Usage:
#   bash scripts/run_ci.sh [--full]
#
# Options:
#   --full    Run full eval including LLM-as-Judge (costs API tokens)
#   (default) Run CI-required tests only (no LLM cost)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FULL_EVAL=false
if [[ "${1:-}" == "--full" ]]; then
    FULL_EVAL=true
fi

echo "=============================================="
echo "  CI Pipeline — Course Finder"
echo "=============================================="
echo ""

# Step 1: Guardrail tests (no API cost)
echo "--- Step 1: Guardrail Tests ---"
docker compose exec ai-service pytest tests/eval/test_guardrails.py -v --tb=short
echo ""

# Step 2: Routing and direct handling tests
echo "--- Step 2: Agent Routing Tests ---"
docker compose exec ai-service pytest tests/eval/test_routing.py tests/eval/test_direct_handling.py -v --tb=short
echo ""

if [ "$FULL_EVAL" = true ]; then
    # Step 3: Full eval suite (costs API tokens)
    echo "--- Step 3: Full Evaluation Suite ---"
    docker compose exec ai-service pytest tests/eval/ -v --tb=short
    echo ""

    # Step 4: Threshold check
    echo "--- Step 4: Quality Gate Check ---"
    if [ -d "$PROJECT_ROOT/evals/results" ] && [ "$(ls -A "$PROJECT_ROOT/evals/results"/*.json 2>/dev/null)" ]; then
        python "$SCRIPT_DIR/check_thresholds.py"
    else
        echo "SKIP: No eval results found. Run eval_search.py first."
    fi
else
    echo "--- Skipping full eval (use --full to include) ---"
fi

echo ""
echo "=============================================="
echo "  CI Pipeline Complete"
echo "=============================================="
