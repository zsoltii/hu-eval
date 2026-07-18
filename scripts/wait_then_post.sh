#!/bin/bash
# wait_then_post.sh — Vár a HuLU/MMLU followup befejezésére, majd elindítja
# a post_followup.sh-t.

set -e
PROJ="/home/openclaw/.openclaw/wiki/hu-eval"
HULU_PID="$1"
MMLU_PID="$2"

echo "$(date): wait_then_post indítása (HULU=$HULU_PID, MMLU=$MMLU_PID)"

# Vár a HuLU-ra
while kill -0 "$HULU_PID" 2>/dev/null; do
    sleep 60
done
echo "$(date): HuLU followup kész"

# Vár a MMLU-ra
while kill -0 "$MMLU_PID" 2>/dev/null; do
    sleep 60
done
echo "$(date): MMLU followup kész"

# Post followup indítása
bash "$PROJ/scripts/post_followup.sh"
