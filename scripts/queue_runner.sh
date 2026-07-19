#!/bin/bash
set -u
cd /home/openclaw/.openclaw/wiki/hu-eval

QUEUE_LOG="logs/queue_runner_$(date +%Y%m%d_%H%M).log"
echo "$(date) - queue_runner indul: $QUEUE_LOG" | tee "$QUEUE_LOG"

# Benchmark modellek — judge modellek (deepseek-v4-pro:cloud) NEM kerülnek ide.
# A kimi-k2.6:cloud benchmark modellként fut (bíró státusz törölve v1.2.4).
# A minimax-m2.5:cloud és minimax-m2.7:cloud törölve (régi modellek, 2026-06-08).
# A deepseek-v4-pro:cloud és minimax-m3:cloud think módjai 2026-06-09 hozzáadva.
# A qwen3-next:80b-cloud 2026-06-10 hozzáadva (80B paraméter, FP8, 262K context).
MODELS=(
  "qwen3.5:cloud"
  "qwen3-next:80b-cloud"
  "gpt-oss:120b-cloud"
  "kimi-k2.6:cloud"
  "glm-5.1:cloud"
  "glm-5.2:cloud"
  "nemotron-3-ultra:cloud"
  "deepseek-v4-flash:cloud"
  "deepseek-v4-pro:cloud"
  "minimax-m3:cloud"
  "gpt-oss:20b-cloud"
)

# Két mód: nothink (alapértelmezett, gyors) és think (lassabb, de jobb minőség)
MODES=("nothink" "think")

for MODEL in "${MODELS[@]}"; do
  MODEL_SAFE_BASE=$(echo "$MODEL" | tr ':/' '--')

  for MODE in "${MODES[@]}"; do
    # Skip-check: ellenőrzi mindkét útvonalat
    # - Új: results/{model}-{mode}/hulu_results.jsonl (az új kóddal futtatva)
    # - Régi: results/{model}/hulu_results.jsonl (a régi kóddal futtatva, mode nélkül)
    NEW_RESULTS="results/${MODEL_SAFE_BASE}-${MODE}/hulu_results.jsonl"
    OLD_RESULTS="results/${MODEL_SAFE_BASE}/hulu_results.jsonl"

    SKIP=false
    if [ -f "$NEW_RESULTS" ] && [ "$(wc -l < "$NEW_RESULTS" 2>/dev/null || echo 0)" -ge 2581 ]; then
      SKIP=true
      REASON="új formátum"
    elif [ -f "$OLD_RESULTS" ] && [ "$(wc -l < "$OLD_RESULTS" 2>/dev/null || echo 0)" -ge 2581 ]; then
      SKIP=true
      REASON="régi formátum"
    fi

    if $SKIP; then
      echo "$(date) - $MODEL ($MODE): már kész ($REASON), kihagyás." | tee -a "$QUEUE_LOG"
      continue
    fi

    echo "$(date) - Benchmark indítása: $MODEL ($MODE)" | tee -a "$QUEUE_LOG"
    TS=$(date +%Y%m%d_%H%M)
    LOG="logs/hulu_${MODEL_SAFE_BASE}-${MODE}_${TS}.log"
    /home/openclaw/anaconda3/envs/eval-hu/bin/python scripts/run_hulu.py --model "$MODEL" --mode "$MODE" > "$LOG" 2>&1
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
      echo "$(date) - $MODEL ($MODE): KÉSZ, exit=0, log: $LOG" | tee -a "$QUEUE_LOG"
    else
      echo "$(date) - $MODEL ($MODE): HIBA, exit=$EXIT_CODE, log: $LOG" | tee -a "$QUEUE_LOG"
    fi
  done
done

echo "$(date) - Minden benchmark modell kész (vagy hibás)." | tee -a "$QUEUE_LOG"
