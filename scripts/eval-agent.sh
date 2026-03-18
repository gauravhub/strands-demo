#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EVALUATOR_CONFIG="$REPO_ROOT/specs/015-agentcore-evaluations/tool-selection-evaluator.json"

EVALUATORS=(
  "Builtin.GoalSuccessRate"
  "Builtin.Helpfulness"
  "Builtin.Correctness"
  "Builtin.Faithfulness"
  "tool_selection_accuracy-EeUCiaBBP3"
)

usage() {
  cat <<EOF
Usage: eval-agent.sh <command> [options]

Commands:
  run <session-id> [--days N] [--output FILE]
      Run on-demand evaluation with all evaluators against the given session.

  setup
      Create online evaluation config with all evaluators at 100% sampling rate.

  list
      List all online evaluation configurations.

  status <config-id>
      Get details of a specific online evaluation configuration.

  create-evaluator
      Register the custom tool_selection_accuracy evaluator.

  list-evaluators
      List all registered evaluators.

Examples:
  eval-agent.sh run sess-abc123
  eval-agent.sh run sess-abc123 --days 7
  eval-agent.sh run sess-abc123 --days 7 --output results.json
  eval-agent.sh setup
  eval-agent.sh list
  eval-agent.sh status config-xyz789
  eval-agent.sh create-evaluator
  eval-agent.sh list-evaluators
EOF
}

case "${1:-}" in
  run)
    shift
    if [[ $# -lt 1 ]]; then
      echo "Error: run requires a <session-id> argument." >&2
      usage
      exit 1
    fi
    SESSION_ID="$1"
    shift

    EXTRA_ARGS=()
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --days)
          EXTRA_ARGS+=("--days" "$2")
          shift 2
          ;;
        --output)
          EXTRA_ARGS+=("--output" "$2")
          shift 2
          ;;
        *)
          echo "Error: Unknown option '$1'" >&2
          exit 1
          ;;
      esac
    done

    EVAL_FLAGS=()
    for ev in "${EVALUATORS[@]}"; do
      EVAL_FLAGS+=("--evaluator" "$ev")
    done

    agentcore eval run \
      "${EVAL_FLAGS[@]}" \
      --session-id "$SESSION_ID" \
      "${EXTRA_ARGS[@]}"
    ;;

  setup)
    agentcore eval online create \
      --name strands_demo_eval \
      --sampling-rate 100.0 \
      --evaluator "Builtin.GoalSuccessRate" \
      --evaluator "Builtin.Helpfulness" \
      --evaluator "Builtin.Correctness" \
      --evaluator "Builtin.Faithfulness" \
      --evaluator "tool_selection_accuracy" \
      --description "Continuous evaluation for strands-demo agent"
    ;;

  list)
    agentcore eval online list
    ;;

  status)
    shift
    if [[ $# -lt 1 ]]; then
      echo "Error: status requires a <config-id> argument." >&2
      usage
      exit 1
    fi
    agentcore eval online get --config-id "$1"
    ;;

  create-evaluator)
    agentcore eval evaluator create \
      --name "tool_selection_accuracy" \
      --config "$EVALUATOR_CONFIG" \
      --level TRACE \
      --description "Evaluates whether the agent selected the correct tools for the user request"
    ;;

  list-evaluators)
    agentcore eval evaluator list
    ;;

  *)
    usage
    ;;
esac
