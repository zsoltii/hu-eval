#!/bin/bash
# priority_judge.sh — A gemini-3-flash-preview bíró megszűnt (2026-07-14), helyette deepseek-v4-pro:cloud.
# Ez a script ELŐSZÖR a bíró-igényes feladatokat futtatja (HuGME, MT-Bench rejudge),
# CSAK UTÁNA az UD refuttatást.

set -e

LOG_DIR="/home/openclaw/.openclaw/wiki/hu-eval/logs"
PROJ="/home/openclaw/.openclaw/wiki/hu-eval"

cd "$PROJ"
source /home/openclaw/anaconda3/etc/profile.d/conda.sh
conda activate eval-hu

echo "$(date): priority_judge indítása (bíró: deepseek-v4-pro:cloud)"
echo "  Prioritás: HuGME rejudge → MT-Bench rejudge → UD refuttatás"
echo ""

# 1. HuGME rejudge — 22 modell × 299 item × 6 metrika = 39 468 bíró hívás
#    Becsült idő: ~22 ó (22 modell × 60p)
echo "════════════════════════════════════════════════════"
echo "  [1/3] HuGME rejudge (deepseek-v4-pro:cloud)"
echo "════════════════════════════════════════════════════"
if [ -f "$LOG_DIR/priority_hugme_done" ]; then
    echo "  ⏭️  Már kész (marker fájl: $LOG_DIR/priority_hugme_done) — átugrás"
else
    python -u "$PROJ/scripts/rejudge_hugme.py" --min-metrics 6 --verbose \
        > "$LOG_DIR/priority_hugme_rejudge.log" 2>&1 || echo "⚠️ HuGME rejudge részben/leállt"
    touch "$LOG_DIR/priority_hugme_done"
    echo "$(date): HuGME rejudge kész" >> "$LOG_DIR/priority_judge.log"
fi

# 2. MT-Bench rejudge — 22 modell × 24 item × 3 baseline × 4 GSB hívás = 6 336 bíró hívás
#    Becsült idő: ~1.3 ó (20 modell × 4p)
echo "════════════════════════════════════════════════════"
echo "  [2/3] MT-Bench rejudge (deepseek-v4-pro:cloud, multi-baseline)"
echo "════════════════════════════════════════════════════"
if [ -f "$LOG_DIR/priority_mt_bench_done" ]; then
    echo "  ⏭️  Már kész (marker fájl: $LOG_DIR/priority_mt_bench_done) — átugrás"
else
    python -u "$PROJ/scripts/rejudge_mt_bench.py" --verbose \
        --baselines deepseek-v4-flash:cloud deepseek-v4-pro:cloud kimi-k2.6:cloud \
        > "$LOG_DIR/priority_mt_bench_rejudge.log" 2>&1 || echo "⚠️ MT-Bench rejudge részben/leállt"
    touch "$LOG_DIR/priority_mt_bench_done"
    echo "$(date): MT-Bench rejudge kész" >> "$LOG_DIR/priority_judge.log"
fi

# 3. UD refuttatás — csak a 13 modellt, akik 0.0% accuracy-t produkáltak
#    (a többieknek van eredménye a reparse_ud.py után)
# nothink: 3 modell (gpt-oss:120b, gpt-oss:20b, minimax-m3)
# think: 10 modell (minden aktív)
echo "════════════════════════════════════════════════════"
echo "  [3/3] UD refuttatás (CoT-aware parser)"
echo "════════════════════════════════════════════════════"

UD_NOTHINK_MODELS=(
    "gpt-oss:120b-cloud"
    "gpt-oss:20b-cloud"
    "minimax-m3:cloud"
)
UD_THINK_MODELS=(
    "deepseek-v4-flash:cloud"
    "deepseek-v4-pro:cloud"
    "glm-5.1:cloud"
    "glm-5.2:cloud"
    "gpt-oss:120b-cloud"
    "gpt-oss:20b-cloud"
    "kimi-k2.6:cloud"
    "minimax-m3:cloud"
    "nemotron-3-ultra:cloud"
    "qwen3.5:cloud"
)

for m in "${UD_NOTHINK_MODELS[@]}"; do
    safe=$(echo "$m" | tr ':/' '--')
    state="$PROJ/state/${safe}-nothink/ud_hungarian.json"
    if [ -f "$state" ]; then
        echo "UD refuttatás (nothink): $m"
        python -u "$PROJ/scripts/run_ud_hungarian.py" --model "$m" --mode nothink --reset \
            > "$LOG_DIR/priority_rerun_ud_$(echo $safe)_nothink.log" 2>&1
    fi
done

for m in "${UD_THINK_MODELS[@]}"; do
    safe=$(echo "$m" | tr ':/' '--')
    state="$PROJ/state/${safe}-think/ud_hungarian.json"
    if [ -f "$state" ]; then
        echo "UD refuttatás (think): $m"
        python -u "$PROJ/scripts/run_ud_hungarian.py" --model "$m" --mode think --reset \
            > "$LOG_DIR/priority_rerun_ud_$(echo $safe)_think.log" 2>&1
    fi
done
touch "$LOG_DIR/priority_ud_done"
echo "$(date): UD refuttatás kész" >> "$LOG_DIR/priority_judge.log"

# 4. Státusz táblázat frissítése
echo "════════════════════════════════════════════════════"
echo "  [4/4] Státusz táblázat frissítése"
echo "════════════════════════════════════════════════════"
python3 /tmp/opencode/build_status_table.py

# Végső log
echo "$(date): priority_judge kész" >> "$LOG_DIR/priority_judge.log"
echo "✅ Minden kész" | tee -a "$LOG_DIR/priority_judge.log"
