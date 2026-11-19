#!/usr/bin/env bash
# Setup synchronous physical streaming replication for PG 17 baseline.
set -euo pipefail

[ -f .env ] && { set -a; . ./.env; set +a; }
PG_USER="${PG_USER:-postgres}"
PG_DB="${PG_DB:-labdb}"
PG_PASS="${DB_ROOT_PASSWORD:-${PG_LAB_PASSWORD:-pg_poc_ephemeral}}"

q_prim() {
    docker exec -e PGPASSWORD="$PG_PASS" pg17_sync_primary psql -v ON_ERROR_STOP=1 -U "$PG_USER" -d "$PG_DB" -tAc "$1"
}

q_stby() {
    docker exec -e PGPASSWORD="$PG_PASS" pg17_sync_standby psql -v ON_ERROR_STOP=1 -U "$PG_USER" -d "$PG_DB" -tAc "$1"
}

for _ in $(seq 1 30); do
    if q_prim "SELECT 1;" >/dev/null 2>&1 && q_stby "SELECT pg_is_in_recovery();" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

q_prim "ALTER SYSTEM SET synchronous_standby_names = 'pg17_sync_standby';" >/dev/null
q_prim "ALTER SYSTEM SET synchronous_commit = 'on';" >/dev/null
q_prim "SELECT pg_reload_conf();" >/dev/null

for _ in $(seq 1 20); do
    st="$(q_prim "SELECT sync_state FROM pg_stat_replication WHERE application_name='pg17_sync_standby';" 2>/dev/null | tr -d '[:space:]' || true)"
    if [ "$st" = "sync" ]; then
        echo "[OK] pg17_sync_primary <-> pg17_sync_standby active (sync_state=sync, synchronous_commit=on)"
        exit 0
    fi
    sleep 1
done

echo "[FAIL] Standby did not reach sync_state=sync"
exit 1
