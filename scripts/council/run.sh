#!/usr/bin/env bash
# scripts/council/run.sh — Council of Experts: parallel free-form discussion
#
# Usage:
#   council "benefitly-expert brainstorming rag-pipeline-principal-engineer" "should we add voice?"
#   council --infer "why is the pipeline broken and plans getting stuck?"
#
# Options:
#   --max-turns N    Safety limit on total messages (default: 25)
#   --model MODEL    Claude model for agents (default: sonnet)
#   --tmux           Use tmux split panes (requires: brew install tmux)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Defaults ────────────────────────────────────────────────────────────────
MAX_TURNS=25
MODEL="sonnet"
USE_TMUX=false
INFER=false
ROLES=""
TOPIC=""

# ─── Available skills for inference ──────────────────────────────────────────
AVAILABLE_SKILLS="benefitly-expert brainstorming rag-pipeline-principal-engineer hipaa-phi-boundary software-engineering-master systematic-debugging plan-navigator-architecture incident-diagnosis-playbook pipeline-stuck-detector stripe-integration-master observability-master prompt-engineering-master users-orgs-expert dual-database-routing encryption-pattern-validator plan-data-isolation-guard audit-pipeline-hardening cognito-user-lifecycle admin-panel-qa dsql-lambda-expert cognito-jwt-auditor plan-reprocessing-orchestrator deduplication-impact-analyzer"

# ─── Colors ──────────────────────────────────────────────────────────────────
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_DIM="\033[2m"
C_RED="\033[1;31m"
C_GREEN="\033[1;32m"
C_YELLOW="\033[1;33m"
C_BLUE="\033[1;34m"
C_MAGENTA="\033[1;35m"
C_CYAN="\033[1;36m"
C_WHITE="\033[1;37m"

PALETTE=("$C_MAGENTA" "$C_CYAN" "$C_YELLOW" "$C_GREEN" "$C_BLUE" "$C_RED")

# ─── Markdown → ANSI renderer ───────────────────────────────────────────────
# Converts markdown syntax to terminal escape codes for rich display
render_md() {
  local line_color="${1:-$C_RESET}"
  local width=${COLUMNS:-100}
  local body_width=$((width - 6))  # account for "│  " prefix
  [ "$body_width" -lt 40 ] && body_width=40

  while IFS= read -r line; do
    # Blank line
    if [ -z "$line" ]; then
      echo -e "${line_color}│${C_RESET}"
      continue
    fi

    # Headings: ### text → bold underlined
    if [[ "$line" =~ ^(#{1,3})[[:space:]]+(.*) ]]; then
      local heading="${BASH_REMATCH[2]}"
      echo -e "${line_color}│${C_RESET}  ${C_BOLD}\033[4m${heading}${C_RESET}"
      continue
    fi

    # Horizontal rules: --- or *** or ___
    if [[ "$line" =~ ^[[:space:]]*([-*_]){3,}[[:space:]]*$ ]]; then
      echo -e "${line_color}│${C_RESET}  ${C_DIM}$(printf '─%.0s' $(seq 1 $((body_width - 2))))${C_RESET}"
      continue
    fi

    # List items: - text or * text or N. text → bullet + text
    local prefix=""
    local content="$line"
    if [[ "$line" =~ ^[[:space:]]*[-*][[:space:]]+(.*) ]]; then
      prefix="  ${C_DIM}•${C_RESET} "
      content="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ ^[[:space:]]*([0-9]+)\.[[:space:]]+(.*) ]]; then
      prefix="  ${C_DIM}${BASH_REMATCH[1]}.${C_RESET} "
      content="${BASH_REMATCH[2]}"
    fi

    # Inline formatting: **bold** → ANSI bold, `code` → ANSI cyan
    content=$(echo "$content" | sed \
      -e 's/\*\*\([^*]*\)\*\*/\\033[1m\1\\033[22m/g' \
      -e 's/`\([^`]*\)`/\\033[36m\1\\033[0m/g' \
    )

    # Word wrap: split on raw text length, then render each wrapped line with prefix
    local raw_content
    raw_content=$(echo -e "$content" | sed 's/\x1b\[[0-9;]*m//g')
    local raw_len=${#raw_content}

    if [ "$raw_len" -le "$body_width" ]; then
      echo -e "${line_color}│${C_RESET}  ${prefix}${content}"
    else
      # Wrap by splitting raw text, then render with ANSI per chunk
      # First line gets prefix (bullet/number), continuations get indent
      local first=true
      echo -e "$content" | fmt -w "$body_width" 2>/dev/null | while IFS= read -r wrapped; do
        if [ "$first" = true ]; then
          echo -e "${line_color}│${C_RESET}  ${prefix}${wrapped}"
          first=false
        else
          echo -e "${line_color}│${C_RESET}    ${wrapped}"
        fi
      done
    fi
  done
}

# ─── Parse args ──────────────────────────────────────────────────────────────
usage() {
  cat <<'EOF'
Council of Experts — parallel free-form multi-agent discussion

Usage:
  mise run council -- "role1 role2 role3" "topic to discuss"
  mise run council -- --infer "natural language topic"

Examples:
  mise run council -- "benefitly-expert brainstorming rag-pipeline-principal-engineer" "should we add voice support?"
  mise run council -- --infer "why is the pipeline broken and plans getting stuck?"
  mise run council -- --infer --max-turns 30 "how should we approach multi-tenant billing?"

Options:
  --infer          Auto-pick relevant experts from the topic
  --max-turns N    Max total messages before ending (default: 25)
  --model MODEL    Claude model for agents (default: sonnet)
  --tmux           Use tmux split panes (requires tmux installed)
  -h, --help       Show this help
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --infer)     INFER=true; shift ;;
    --max-turns) MAX_TURNS="$2"; shift 2 ;;
    --model)     MODEL="$2"; shift 2 ;;
    --tmux)      USE_TMUX=true; shift ;;
    -h|--help)   usage ;;
    --)          shift ;;  # skip -- separator from mise
    *)
      if [ -z "$ROLES" ] && [ "$INFER" = false ]; then
        ROLES="$1"
      else
        TOPIC="${TOPIC:+$TOPIC }$1"
      fi
      shift
      ;;
  esac
done

# Handle infer mode where everything is topic
if [ "$INFER" = true ] && [ -n "$ROLES" ] && [ -z "$TOPIC" ]; then
  TOPIC="$ROLES"
  ROLES=""
elif [ "$INFER" = true ] && [ -n "$ROLES" ] && [ -n "$TOPIC" ]; then
  TOPIC="$ROLES $TOPIC"
  ROLES=""
fi

if [ -z "$TOPIC" ]; then
  echo -e "${C_RED}Error: No topic provided.${C_RESET}"
  usage
fi

# ─── Dependency checks ──────────────────────────────────────────────────────
for cmd in jq claude; do
  if ! command -v "$cmd" &>/dev/null; then
    echo -e "${C_RED}Error: '$cmd' is required but not found.${C_RESET}"
    exit 1
  fi
done

if [ "$USE_TMUX" = true ] && ! command -v tmux &>/dev/null; then
  echo -e "${C_RED}Error: tmux not found. Install with: brew install tmux${C_RESET}"
  exit 1
fi

# ─── Infer roles ─────────────────────────────────────────────────────────────
if [ "$INFER" = true ]; then
  echo -e "${C_DIM}Inferring relevant experts for:${C_RESET} $TOPIC"
  ROLES=$(claude -p --model "$MODEL" "Pick 3-4 of these expert roles most relevant to discuss the following topic.

Topic: '$TOPIC'

Available roles: $AVAILABLE_SKILLS

Return ONLY the role names separated by spaces. No explanation, no formatting, no punctuation — just the space-separated names." 2>/dev/null) || {
    echo -e "${C_RED}Error: Failed to infer roles.${C_RESET}"
    exit 1
  }
  # Clean — remove any non-alphanumeric-dash characters
  ROLES=$(echo "$ROLES" | tr -s ' ' | sed 's/^ *//;s/ *$//')
  echo -e "${C_GREEN}Selected:${C_RESET} $ROLES"
  echo ""
fi

if [ -z "$ROLES" ]; then
  echo -e "${C_RED}Error: No roles specified or inferred.${C_RESET}"
  exit 1
fi

# ─── Setup session ───────────────────────────────────────────────────────────
SESSION_ID=$(date +%s)
COUNCIL_DIR="/tmp/council-${SESSION_ID}"
mkdir -p "$COUNCIL_DIR"
CONV_FILE="$COUNCIL_DIR/conversation.jsonl"
touch "$CONV_FILE"

# Seed the conversation with the topic
jq -nc \
  --arg msg "$TOPIC" \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{id: 1, from: "moderator", timestamp: $ts, message: $msg}' >> "$CONV_FILE"

read -ra ROLE_ARRAY <<< "$ROLES"
ALL_ROLES="${ROLE_ARRAY[*]}"
NUM_AGENTS=${#ROLE_ARRAY[@]}

# Save session metadata
jq -nc \
  --arg topic "$TOPIC" \
  --arg roles "$ALL_ROLES" \
  --argjson max "$MAX_TURNS" \
  --arg model "$MODEL" \
  --arg id "$SESSION_ID" \
  '{session_id: $id, topic: $topic, roles: $roles, max_turns: $max, model: $model}' \
  > "$COUNCIL_DIR/meta.json"

# Build agent-to-color map
declare -A AGENT_COLORS
for i in "${!ROLE_ARRAY[@]}"; do
  AGENT_COLORS["${ROLE_ARRAY[$i]}"]="${PALETTE[$((i % ${#PALETTE[@]}))]}"
done
AGENT_COLORS["moderator"]="$C_WHITE"

# ─── Header ──────────────────────────────────────────────────────────────────
echo -e "${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
echo -e "${C_BOLD}  COUNCIL SESSION${C_RESET}  ${C_DIM}#${SESSION_ID}${C_RESET}"
echo -e ""
echo -e "  ${C_DIM}Topic:${C_RESET}   $TOPIC"
echo -e "  ${C_DIM}Experts:${C_RESET} "
for i in "${!ROLE_ARRAY[@]}"; do
  color="${AGENT_COLORS[${ROLE_ARRAY[$i]}]}"
  echo -e "    ${color}■${C_RESET} ${ROLE_ARRAY[$i]}"
done
echo -e "  ${C_DIM}Turns:${C_RESET}   $MAX_TURNS max  ${C_DIM}Model:${C_RESET} $MODEL"
echo -e "${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
echo ""

# ─── TMUX MODE ───────────────────────────────────────────────────────────────
if [ "$USE_TMUX" = true ]; then
  TMUX_SESSION="council-${SESSION_ID}"
  tmux new-session -d -s "$TMUX_SESSION"

  for i in "${!ROLE_ARRAY[@]}"; do
    ROLE="${ROLE_ARRAY[$i]}"
    if [ "$i" -gt 0 ]; then
      tmux split-window -t "$TMUX_SESSION"
      tmux select-layout -t "$TMUX_SESSION" tiled
    fi
    tmux send-keys -t "$TMUX_SESSION" \
      "bash '${SCRIPT_DIR}/agent.sh' '${ROLE}' '${COUNCIL_DIR}' '${ALL_ROLES}' '${MAX_TURNS}' '${MODEL}' '${TOPIC}'" C-m
  done

  # Add a viewer pane
  tmux split-window -t "$TMUX_SESSION"
  tmux select-layout -t "$TMUX_SESSION" tiled
  tmux send-keys -t "$TMUX_SESSION" \
    "tail -f '${CONV_FILE}' | jq -r '\"[\\(.from)] \\(.message)\"'" C-m

  echo "Attaching to tmux session. Detach: Ctrl+B then D"
  echo "Kill session: tmux kill-session -t $TMUX_SESSION"
  tmux attach -t "$TMUX_SESSION"
  exit 0
fi

# ─── SINGLE TERMINAL MODE ───────────────────────────────────────────────────
PIDS=()

# Launch agents in background
for ROLE in "${ROLE_ARRAY[@]}"; do
  bash "${SCRIPT_DIR}/agent.sh" "$ROLE" "$COUNCIL_DIR" "$ALL_ROLES" "$MAX_TURNS" "$MODEL" "$TOPIC" &
  PIDS+=($!)
done

# Cleanup handler
cleanup() {
  echo -e "\n${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
  echo -e "${C_BOLD}  COUNCIL ENDED${C_RESET}"
  echo -e "${C_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"

  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done

  # Generate transcript
  TRANSCRIPT="$COUNCIL_DIR/transcript.md"
  {
    echo "# Council Transcript"
    echo ""
    echo "**Topic:** $TOPIC"
    echo "**Experts:** $ALL_ROLES"
    echo "**Date:** $(date)"
    echo "**Session:** $SESSION_ID"
    echo ""
    echo "---"
    echo ""

    while IFS= read -r line; do
      from=$(echo "$line" | jq -r .from 2>/dev/null) || continue
      msg=$(echo "$line" | jq -r .message 2>/dev/null) || continue
      ts=$(echo "$line" | jq -r .timestamp 2>/dev/null) || continue
      echo "### [$from] — $ts"
      echo ""
      echo "$msg"
      echo ""
    done < "$CONV_FILE"
  } > "$TRANSCRIPT"

  local msg_count
  msg_count=$(wc -l < "$CONV_FILE" | tr -d ' ')
  echo ""
  echo -e "  ${C_DIM}Messages:${C_RESET}    $msg_count"
  echo -e "  ${C_DIM}Transcript:${C_RESET}  $TRANSCRIPT"
  echo -e "  ${C_DIM}Raw data:${C_RESET}    $COUNCIL_DIR"
  echo ""
  exit 0
}
trap cleanup SIGINT SIGTERM

# ─── Live conversation viewer ────────────────────────────────────────────────
LAST_SEEN=0

while true; do
  CURRENT=$(wc -l < "$CONV_FILE" | tr -d ' ')

  if [ "$CURRENT" -gt "$LAST_SEEN" ]; then
    # Read new messages
    while IFS= read -r line; do
      from=$(echo "$line" | jq -r .from 2>/dev/null) || continue
      msg=$(echo "$line" | jq -r .message 2>/dev/null) || continue
      ts=$(echo "$line" | jq -r '.timestamp | split("T")[1] | split(".")[0] // .[0:8]' 2>/dev/null) || ts=""

      COLOR="${AGENT_COLORS[$from]:-$C_WHITE}"

      # Header
      echo -e "${COLOR}┌─── ${C_BOLD}${from}${C_RESET} ${C_DIM}${ts}${C_RESET}"

      # Message body — render markdown to ANSI
      echo "$msg" | render_md "$COLOR"

      # Footer
      local fw=${COLUMNS:-100}
      echo -e "${COLOR}└$( printf '─%.0s' $(seq 1 $((fw - 2))) )${C_RESET}"
      echo ""
    done < <(tail -n +"$((LAST_SEEN + 1))" "$CONV_FILE")

    LAST_SEEN=$CURRENT

    # Check if done
    if [ "$CURRENT" -ge "$MAX_TURNS" ]; then
      echo -e "${C_BOLD}Max turns reached ($MAX_TURNS).${C_RESET}"
      cleanup
    fi

    # Check if all agents exited
    alive=0
    for pid in "${PIDS[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        alive=$((alive + 1))
      fi
    done
    if [ "$alive" -eq 0 ]; then
      echo -e "${C_DIM}All agents have exited.${C_RESET}"
      sleep 2  # let final messages flush
      cleanup
    fi
  fi

  sleep 1
done
