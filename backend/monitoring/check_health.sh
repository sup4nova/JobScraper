#!/bin/sh
# Read-only health check for the jobscrapper-bot container, meant to be run
# over SSH by the "VPS Bot Monitor" GitHub Action (.github/workflows/vps-monitor.yml).
#
# Always exits 0 — the caller decides pass/fail by grepping this script's
# output (for ALERT:/Traceback/CONTAINER_DOWN), not by the exit code. This is
# also the command forced via `command=` in authorized_keys for the dedicated
# monitoring SSH key, so it never takes arguments from the caller.
set -u

STATUS=$(docker inspect -f '{{.State.Status}}' jobscrapper-bot 2>/dev/null || echo "missing")
if [ "$STATUS" != "running" ]; then
    echo "CONTAINER_DOWN status=$STATUS"
fi

# Patterns below cover two levels:
#   - ALERT:/Traceback           -> global failure (all sources empty, or an
#                                    uncaught crash)
#   - the rest                   -> a single source detected as blocked
#                                    (not just "0 results", which can be a
#                                    legitimate empty search — these are the
#                                    specific messages each scraper prints
#                                    when it recognizes an anti-bot wall or
#                                    an actual exception, not just a quiet day)
docker logs --since 3h jobscrapper-bot 2>&1 | grep -E \
    "ALERT:|Traceback \(most recent call last\)|Cloudflare|job list never appeared|selectors may be outdated|(Indeed|LinkedIn|Wellfound|Remote OK) error:" \
    || echo "OK: no alert pattern in the last 3h"
