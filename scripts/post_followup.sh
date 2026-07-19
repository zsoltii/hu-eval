#!/bin/bash
# post_followup.sh — A HuLU/MMLU followup befejezése után futtatandó javítások:
# 1. UD Hungarian: 13 modell refuttatása (gpt-oss-120b/20b/minimax-m3 nothink + 10 think)
# 2. HuGME rejudge (22 modell, 6 metrika/item)
# 3. MT-Bench rejudge (20 modell, 3 baseline)
# 4. Státusz táblázat frissítése

set -e

LOG_DIR="./logs"
PROJ="."

cd "$PROJ"
source "$HOME/anaconda3/etc/profile.d/conda.sh"
conda activate eval-hu

echo "$(date): post_followup indítása"

# UD refuttatás — csak a 13 modellt, akik 0.0% accuracy-t produkáltak
# (a többieknek van eredménye a reparse_ud.py után)
# nothink: 3 modell (gpt-oss-120b, gpt-oss-20b, minimax-m3)
# think: 10 modell (minden aktív)

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

# UD reset és refuttatás
for m in "${UD_NOTHINK_MODELS[@]}"; do
    safe=$(echo "$m" | tr ':/' '--')
    state="$PROJ/state/${safe}-nothink/ud_hungarian.json"
    if [ -f "$state" ]; then
        echo "UD refuttatás (nothink): $m"
        python -u "$PROJ/scripts/run_ud_hungarian.py" --model "$m" --mode nothink --reset \
            > "$LOG_DIR/rerun_ud_$(echo $safe)_nothink.log" 2>&1
    fi
done

for m in "${UD_THINK_MODELS[@]}"; do
    safe=$(echo "$m" | tr ':/' '--')
    state="$PROJ/state/${safe}-think/ud_hungarian.json"
    if [ -f "$state" ]; then
        echo "UD refuttatás (think): $m"
        python -u "$PROJ/scripts/run_ud_hungarian.py" --model "$m" --mode think --reset \
            > "$LOG_DIR/rerun_ud_$(echo $safe)_think.log" 2>&1
    fi
done

# HuGME rejudge (sorban, mert sokáig tart)
echo "HuGME rejudge indítása"
python -u "$PROJ/scripts/rejudge_hugme.py" --min-metrics 6 \
    > "$LOG_DIR/rejudge_hugme_post.log" 2>&1

# MT-Bench rejudge multi-baseline-nal
echo "MT-Bench rejudge indítása"
python -u "$PROJ/scripts/rejudge_mt_bench.py" \
    --baselines deepseek-v4-flash:cloud deepseek-v4-pro:cloud kimi-k2.6:cloud \
    > "$LOG_DIR/rejudge_mt_bench_post.log" 2>&1

# Státusz táblázat frissítése
echo "Státusz táblázat frissítése"
python3 /tmp/opencode/build_status_table.py

# Végső log
echo "$(date): post_followup kész" >> "$LOG_DIR/post_followup.log"
echo "✅ Minden kész" | tee -a "$LOG_DIR/post_followup.log"
