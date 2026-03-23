#!/usr/bin/env bash
# scripts/council/agent.sh — Silent agent loop for council discussions
# Polls conversation.jsonl, decides whether to respond, appends response.
# All display output goes to stderr (captured or shown depending on mode).
set -euo pipefail

ROLE="$1"
COUNCIL_DIR="$2"
ALL_ROLES="$3"
MAX_TURNS="${4:-20}"
MODEL="${5:-sonnet}"
TOPIC="${6:-}"

CONV_FILE="$COUNCIL_DIR/conversation.jsonl"
LOCK_DIR="$COUNCIL_DIR/.lock"
MY_LOG="$COUNCIL_DIR/${ROLE}.log"

last_seen=0
my_last_spoke=0        # message ID when I last spoke
consecutive_passes=0

log() { echo "[$(date +%H:%M:%S)] [$ROLE] $*" >> "$MY_LOG"; }

# Atomic append using mkdir lock (portable, no flock needed on macOS)
append_message() {
  local msg="$1"
  local retries=0
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    sleep 0.1
    retries=$((retries + 1))
    if [ "$retries" -gt 50 ]; then
      log "WARN: lock timeout, writing anyway"
      break
    fi
  done

  local new_id
  new_id=$(( $(wc -l < "$CONV_FILE" | tr -d ' ') + 1 ))
  jq -nc \
    --argjson id "$new_id" \
    --arg from "$ROLE" \
    --arg msg "$msg" \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{id: $id, from: $from, timestamp: $ts, message: $msg}' >> "$CONV_FILE"

  rmdir "$LOCK_DIR" 2>/dev/null || true
  my_last_spoke=$new_id
  log "Responded (msg #$new_id)"
}

build_prompt() {
  local history
  history=$(tail -30 "$CONV_FILE" | jq -r '"[\(.from)] \(.message)"' 2>/dev/null || echo "")

  local other_roles
  other_roles=$(echo "$ALL_ROLES" | tr ' ' '\n' | grep -v "^${ROLE}$" | tr '\n' ', ' | sed 's/,$//')

  cat <<PROMPT
You are "${ROLE}", an expert participating in a council discussion about the Benefitly project.

TOPIC: ${TOPIC}

YOUR FELLOW COUNCIL MEMBERS: ${other_roles}

CONVERSATION SO FAR:
${history}

RULES:
1. Respond with your expert perspective — be opinionated, specific, and concise
2. Keep responses to 2-4 short paragraphs maximum
3. Build on others' points or respectfully challenge them when you disagree
4. Address other members by name when responding to their points
5. If you genuinely have nothing new to add right now, respond with exactly: PASS
6. Do NOT repeat what others have already said
7. Do NOT be generic — make your expertise count
8. When you have a concrete recommendation, state it clearly
9. Use markdown formatting: **bold** for key terms, \`code\` for technical references, bullet lists for recommendations

Respond now as ${ROLE}:
PROMPT
}

log "Agent started. Model=$MODEL, MaxTurns=$MAX_TURNS"

# Initial delay — stagger agent starts (1-5s based on role hash)
hash_delay=$(( $(echo "$ROLE" | cksum | cut -d' ' -f1) % 5 + 1 ))
sleep "$hash_delay"

while true; do
  current=$(wc -l < "$CONV_FILE" | tr -d ' ')

  # Check max turns
  if [ "$current" -ge "$MAX_TURNS" ]; then
    log "Max turns reached ($MAX_TURNS). Exiting."
    exit 0
  fi

  if [ "$current" -gt "$last_seen" ]; then
    last_seen=$current

    # Who spoke last?
    latest_from=$(tail -1 "$CONV_FILE" | jq -r .from 2>/dev/null || echo "")

    # Skip if I just spoke
    if [ "$latest_from" = "$ROLE" ]; then
      sleep 2
      continue
    fi

    # Cooldown: wait for at least 2 messages from others after my last response
    if [ "$my_last_spoke" -gt 0 ] && [ $((current - my_last_spoke)) -lt 2 ]; then
      log "Cooldown — only $((current - my_last_spoke)) messages since I last spoke"
      sleep 3
      continue
    fi

    # Random thinking delay (2-6s) to create natural conversation flow
    think_delay=$(( RANDOM % 5 + 2 ))
    log "Thinking for ${think_delay}s..."
    sleep "$think_delay"

    # Re-check: someone else may have responded while we were thinking
    current=$(wc -l < "$CONV_FILE" | tr -d ' ')
    last_seen=$current

    # Build prompt and ask claude
    prompt=$(build_prompt)
    log "Calling claude..."

    response=$(echo "$prompt" | claude -p --model "$MODEL" 2>/dev/null) || {
      log "ERROR: claude call failed"
      sleep 5
      continue
    }

    # Clean response
    response=$(echo "$response" | sed '/^$/{ N; /^\n$/d; }' | head -50)

    if [ -z "$response" ]; then
      log "Empty response, treating as PASS"
      consecutive_passes=$((consecutive_passes + 1))
    elif echo "$response" | grep -qx "PASS"; then
      log "PASS"
      consecutive_passes=$((consecutive_passes + 1))
    else
      append_message "$response"
      consecutive_passes=0
    fi
  fi

  # Adaptive polling: slower if nothing is happening
  if [ "$consecutive_passes" -ge 3 ]; then
    sleep 8
  else
    sleep 3
  fi
done
