#!/bin/bash
set -u
cd /home/openclaw/.openclaw/wiki/hu-eval

QUEUE_LOG="logs/queue_all_$(date +%Y%m%d_%H%M).log"
echo "$(date) - queue_all_benchmarks indul: $QUEUE_LOG" | tee "$QUEUE_LOG"

BENCHMARKS=("hulu" "mmlu_hu" "hugme" "mt_bench_hu" "ud_hungarian")
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
MODES=("nothink" "think")

# Benchmark-specifikus várt sorok a results JSONL-ben
declare -A EXPECTED_LINES
EXPECTED_LINES["hulu"]=2581
EXPECTED_LINES["mmlu_hu"]=1880
EXPECTED_LINES["hugme"]=299
EXPECTED_LINES["mt_bench_hu"]=24
EXPECTED_LINES["ud_hungarian"]=449

for BENCH in "${BENCHMARKS[@]}"; do
  EXPECTED="${EXPECTED_LINES[$BENCH]:-0}"

  for MODEL in "${MODELS[@]}"; do
    MODEL_SAFE_BASE=$(echo "$MODEL" | tr ':/' '--')

    for MODE in "${MODES[@]}"; do
      MODEL_SAFE="${MODEL_SAFE_BASE}-${MODE}"

      # Skip-check: results JSONL megléte + elég sor
      RESULTS_FILE="results/${MODEL_SAFE}/${BENCH}_results.jsonl"
      SKIP=false
      if [ -f "$RESULTS_FILE" ] && [ "$(wc -l < "$RESULTS_FILE" 2>/dev/null || echo 0)" -ge "$EXPECTED" ]; then
        SKIP=true
      fi

      if $SKIP; then
        echo "$(date) - $BENCH $MODEL ($MODE): már kész (${EXPECTED}+ sor), kihagyás." | tee -a "$QUEUE_LOG"
        continue
      fi

      echo "$(date) - Benchmark indítása: $BENCH $MODEL ($MODE)" | tee -a "$QUEUE_LOG"
      TS=$(date +%Y%m%d_%H%M)
      LOG="logs/${BENCH}_${MODEL_SAFE}_${TS}.log"
      /home/openclaw/anaconda3/envs/eval-hu/bin/python "scripts/run_${BENCH}.py" \
        --model "$MODEL" --mode "$MODE" > "$LOG" 2>&1
      EXIT_CODE=$?
      if [ $EXIT_CODE -eq 0 ]; then
        echo "$(date) - $BENCH $MODEL ($MODE): KÉSZ, exit=0" | tee -a "$QUEUE_LOG"
      else
        echo "$(date) - $BENCH $MODEL ($MODE): HIBA, exit=$EXIT_CODE, log: $LOG" | tee -a "$QUEUE_LOG"
        continue  # további modellekre nem állunk meg (queue_runner mintára)
      fi

      # Judge lépés HuGME és MT-Bench esetén
      if [ "$BENCH" = "hugme" ]; then
        echo "$(date) - Judge indítása: $BENCH $MODEL ($MODE)" | tee -a "$QUEUE_LOG"
        /home/openclaw/anaconda3/envs/eval-hu/bin/python scripts/judge_hugme.py \
          --model "$MODEL" --mode "$MODE" >> "$LOG" 2>&1
        echo "$(date) - Judge: $BENCH $MODEL ($MODE): $?" | tee -a "$QUEUE_LOG"
      fi

      if [ "$BENCH" = "mt_bench_hu" ]; then
        echo "$(date) - Judge indítása: $BENCH $MODEL ($MODE)" | tee -a "$QUEUE_LOG"
        /home/openclaw/anaconda3/envs/eval-hu/bin/python scripts/judge_mt_bench.py \
          --model "$MODEL" --mode "$MODE" >> "$LOG" 2>&1
        echo "$(date) - Judge: $BENCH $MODEL ($MODE): $?" | tee -a "$QUEUE_LOG"
      fi
    done
  done
done

echo "$(date) - Minden benchmark kész (vagy hibás)." | tee -a "$QUEUE_LOG"
