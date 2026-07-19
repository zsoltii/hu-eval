#!/bin/bash
set -u
cd "$(dirname "$0")/.."

WAIT_PID_FILE="logs/queue_runner.pid"
QUEUE_LOG="logs/queue_runner_$(date +%Y%m%d_%H%M).log"  # placeholder, figyeljük a PID fájlt

# Várakozás a queue runner PID-jére (a fájlból olvassuk, hogy mindig az aktuális legyen)
LAST_PID=""
while true; do
  CUR_PID=$(cat "$WAIT_PID_FILE" 2>/dev/null)
  if [ -z "$CUR_PID" ]; then
    echo "$(date) - Nincs queue runner PID fájl, kilépés."
    break
  fi
  if [ "$CUR_PID" != "$LAST_PID" ]; then
    echo "$(date) - Queue runner PID: $CUR_PID (várakozás...)"
    LAST_PID="$CUR_PID"
  fi
  if ! ps -p "$CUR_PID" > /dev/null 2>&1; then
    # Ha a queue runner leállt, ellenőrizzük, hogy van-e újabb PID
    sleep 30
    NEW_PID=$(cat "$WAIT_PID_FILE" 2>/dev/null)
    if [ -z "$NEW_PID" ] || [ "$NEW_PID" = "$CUR_PID" ]; then
      echo "$(date) - A queue_runner (PID $CUR_PID) befejeződött, nem indult új."
      break
    fi
  else
    sleep 120
  fi
done

PHASE2_LOG="logs/phase2_runner_$(date +%Y%m%d_%H%M).log"
echo "$(date) - phase2_runner indul: $PHASE2_LOG" | tee "$PHASE2_LOG"

# A nothink mód eredményei a results/{model}-nothink/ mappákban vannak
# A think mód eredményei a results/{model}-think/ mappákban lesznek
# A phase2 a think módot futtatja minden modellre (a queue a nothink-et)
# DE: a queue runner most MINDKÉT módot futtatja, tehát a phase2-nek nincs dolga.
# Ez a script csak biztonsági háló: ha a queue runner leáll, és maradt think mód,
# akkor a phase2 folytatja.

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

for MODEL in "${MODELS[@]}"; do
  MODEL_SAFE=$(echo "$MODEL" | tr ':/' '--')
  # Csak a think módot ellenőrizzük (a nothink-et a queue runner csinálta)
  RESULTS_FILE="results/${MODEL_SAFE}-think/hulu_results.jsonl"
  if [ -f "$RESULTS_FILE" ] && [ "$(wc -l < "$RESULTS_FILE" 2>/dev/null || echo 0)" -ge 2581 ]; then
    echo "$(date) - $MODEL (think): már kész, kihagyás." | tee -a "$PHASE2_LOG"
    continue
  fi
  echo "$(date) - $MODEL (think): indítás (RESUME ha van checkpoint)" | tee -a "$PHASE2_LOG"
  TS=$(date +%Y%m%d_%H%M)
  LOG="logs/hulu_${MODEL_SAFE}-think_phase2_${TS}.log"
  $HOME/anaconda3/envs/eval-hu/bin/python scripts/run_hulu.py --model "$MODEL" --mode think > "$LOG" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date) - $MODEL (think): KÉSZ" | tee -a "$PHASE2_LOG"
  else
    echo "$(date) - $MODEL (think): HIBA, exit=$EXIT_CODE" | tee -a "$PHASE2_LOG"
  fi
done
echo "$(date) - Phase2 kész." | tee -a "$PHASE2_LOG"
