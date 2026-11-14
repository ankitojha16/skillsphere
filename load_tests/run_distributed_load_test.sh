#!/usr/bin/env bash
# SkillSphere Phase 18 — Distributed Load Testing Automation
# Usage: ./load_tests/run_distributed_load_test.sh [TARGET_USERS] [HOST_URL]

set -euo pipefail

TARGET_USERS="${1:-1000}"
HOST_URL="${2:-http://localhost:8000}"
RUN_TIME="60s"
SPAWN_RATE=100

echo "=========================================================="
echo " SkillSphere Phase 18 Distributed Load Test"
echo " Target Concurrent Users: ${TARGET_USERS}"
echo " Host Target:             ${HOST_URL}"
echo " Duration:                ${RUN_TIME}"
echo " Spawn Rate:              ${SPAWN_RATE} users/sec"
echo "=========================================================="

LOCUST_BIN="locust"
if [ -f "./.venv/bin/locust" ]; then
  LOCUST_BIN="./.venv/bin/locust"
fi

${LOCUST_BIN} \
  -f load_tests/locustfile_phase18.py \
  --headless \
  --users "${TARGET_USERS}" \
  --spawn-rate "${SPAWN_RATE}" \
  --run-time "${RUN_TIME}" \
  --host "${HOST_URL}" \
  --html "load_tests/report_${TARGET_USERS}_ccu.html" \
  --csv "load_tests/stats_${TARGET_USERS}_ccu"

echo "[+] Load test complete. Report saved to load_tests/report_${TARGET_USERS}_ccu.html"
