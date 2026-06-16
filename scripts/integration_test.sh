#!/usr/bin/env bash
# Integration test — runs the Agent across multiple parameter combinations
# and validates that every output contains the required fields.
#
# Usage:
#   chmod +x scripts/integration_test.sh
#   ./scripts/integration_test.sh
#
# Returns 0 if all scenarios pass, 1 otherwise.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
FAILURES=()

# Required keys that every Agent output dict must contain.
REQUIRED_KEYS=(
    "cluster"
    "primitive"
    "topology"
    "topology_graph_summary"
    "candidate_algorithms"
    "algorithm"
    "reason"
    "result"
    "best_algorithm"
    "best_result"
    "ranking"
    "strategy"
)

# Test scenarios:  nodes  msg_size(MB)  primitive
SCENARIOS=(
    # Tiny KB-level
    "8   0.03   AllReduce"
    "8   0.03   AllGather"
    "8   0.03   ReduceScatter"
    # Small message
    "8   0.5    AllReduce"
    # Medium message, various primitives
    "8   128    AllReduce"
    "8   128    AllGather"
    "8   128    ReduceScatter"
    # Large message, multi-node
    "16  800    AllReduce"
    "64  800    AllGather"
    # Huge message, large-scale
    "128 2048   ReduceScatter"
    "256 4096   AllReduce"
)

echo "============================================"
echo " HCCL-Agent Integration Test"
echo " Scenarios: ${#SCENARIOS[@]}"
echo "============================================"
echo ""

run_one() {
    local nodes="$1"
    local msg="$2"
    local prim="$3"

    printf "  [%2d nodes, %7s MB, %-14s] " "$nodes" "$msg" "$prim"

    # Run the Agent via a short Python script that validates the output
    # structure and exits non-zero on missing keys.
    if python3 -c "
import json, sys
sys.path.insert(0, '$PROJECT_ROOT')
from agent.hccl_agent import HCCLAgent

agent = HCCLAgent()
output = agent.run(nodes=$nodes, message_size=$msg, primitive='$prim')

required = ${REQUIRED_KEYS[@]@Q}
missing = [k for k in required if k not in output]
if missing:
    print('FAIL — missing keys:', missing, file=sys.stderr)
    sys.exit(1)

# Validate sub-structures
br = output.get('best_result', {})
if not all(k in br for k in ('latency', 'bandwidth', 'score')):
    print('FAIL — best_result incomplete', file=sys.stderr)
    sys.exit(1)

strat = output.get('strategy', {})
if 'steps' not in strat:
    print('FAIL — strategy missing steps', file=sys.stderr)
    sys.exit(1)

rank = output.get('ranking', [])
if not isinstance(rank, list) or len(rank) == 0:
    print('FAIL — ranking empty', file=sys.stderr)
    sys.exit(1)

topo_sum = output.get('topology_graph_summary', {})
if 'num_nodes' not in topo_sum:
    print('FAIL — topology_graph_summary incomplete', file=sys.stderr)
    sys.exit(1)

print('PASS')
" 2>&1; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
        FAILURES+=("nodes=$nodes msg=$msg prim=$prim")
    fi
}

for scenario in "${SCENARIOS[@]}"; do
    # Skip empty lines.
    [[ -z "$scenario" ]] && continue
    read -r n m p <<< "$scenario"
    run_one "$n" "$m" "$p"
done

echo ""
echo "============================================"
echo " Results: $PASS passed, $FAIL failed"
echo "============================================"

if [[ $FAIL -gt 0 ]]; then
    echo ""
    echo "Failures:"
    for f in "${FAILURES[@]}"; do
        echo "  - $f"
    done
    exit 1
else
    echo "All integration tests passed."
    exit 0
fi
