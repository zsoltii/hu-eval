#!/bin/bash
# watchdog_priority.sh — 15 percenként ellenőrzi a priority_judge.sh futását.
# Ha a parent bash leállt, de a feladatok nem készültek el, újraindítja onnan,
# ahol abbahagyta (a rejudge scriptek resume-képesek).
#
# Addig fut, amíg mind a 3 fázis (HuGME, MT-Bench, UD) kész nem lesz.

set -u

PROJ="."
LOG_DIR="$PROJ/logs"
WD_LOG="$LOG_DIR/watchdog.log"

CHECK_INTERVAL=900  # 15 perc

# E-mail/slack értesítés nélkül — csak log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $*" | tee -a "$WD_LOG"
}

# Fázis kész állapotának ellenőrzése
phase_done() {
    local marker="$1"
    [ -f "$LOG_DIR/$marker" ]
}

# Parent bash fut-e?
parent_running() {
    pgrep -f "bash scripts/priority_judge.sh" > /dev/null
}

# Python fut-e a parent alatt?
python_running() {
    pgrep -f "rejudge_hugme\|rejudge_mt_bench\|run_ud_hungarian" > /dev/null
}

# Restart helper
restart_priority() {
    log "🔄 priority_judge.sh újraindítása (háttérben, nohup, conda eval-hu)"
    nohup bash -c "
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
        conda activate eval-hu
        cd "$PROJ"
        bash scripts/priority_judge.sh
    " >> "$LOG_DIR/priority_judge.log" 2>&1 &
    disown
    sleep 5
    local pid=$(pgrep -f "bash scripts/priority_judge.sh" | head -1)
    log "   Új parent PID: $pid"
}

# Státusz riport
print_status() {
    local parent=$(pgrep -f "bash scripts/priority_judge.sh" | head -1)
    local py=$(pgrep -f "rejudge_hugme\|rejudge_mt_bench\|run_ud_hungarian" | head -1)
    log "  Státusz: parent=${parent:-leállt}, python=${py:-leállt}"
    log "  Fázis jelzők:"
    for marker in priority_hugme_done priority_mt_bench_done priority_ud_done; do
        if [ -f "$LOG_DIR/$marker" ]; then
            log "    ✅ $marker"
        else
            log "    ⏳ $marker (nem kész)"
        fi
    done
    # Legutolsó log sorok
    log "  Utolsó 3 sor a priority_hugme_rejudge.log-ból:"
    tail -3 "$LOG_DIR/priority_hugme_rejudge.log" 2>/dev/null | sed 's/^/    /' >> "$WD_LOG"
}

# Main loop
log "════════════════════════════════════════════════════════"
log "Watchdog indítása (ellenőrzés minden $CHECK_INTERVAL sec)"
log "════════════════════════════════════════════════════════"

while true; do
    # Mind a 3 fázis kész? → kilépés
    if phase_done "priority_hugme_done" && phase_done "priority_mt_bench_done" && phase_done "priority_ud_done"; then
        log "✅ Mind a 3 fázis kész. Watchdog kilép."
        break
    fi

    # Státusz
    print_status

    # Döntés
    if parent_running; then
        # Parent bash fut → normál eset
        if python_running; then
            log "  ✅ Minden fut, OK."
        else
            # Parent él, de a python child leállt — ez normális a fázisok között
            # (priority_judge.sh-ban a python parancs után || echo, tehát továbblép)
            # DE ha hosszú ideig nincs python, akkor a script is elakadt
            log "  ⚠️ Parent fut, de nincs python child — ellenőrizd a logot!"
        fi
    else
        # Parent bash leállt — kell-e újraindítani?
        if phase_done "priority_hugme_done" && phase_done "priority_mt_bench_done" && phase_done "priority_ud_done"; then
            log "  Mind a 3 fázis kész, parent bash kilépett (normális)."
            break
        else
            log "  ❌ Parent bash leállt, DE a fázisok nem készültek el — újraindítás!"
            restart_priority
        fi
    fi

    log "  Következő ellenőrzés: $CHECK_INTERVAL sec múlva..."
    sleep "$CHECK_INTERVAL"
done

log "════════════════════════════════════════════════════════"
log "Watchdog befejezve ($(date))"
log "════════════════════════════════════════════════════════"
