#!/bin/bash
# Runs every helper command named in SKILL.md and recipes.md against live data. Exits 1 if any fails.
set -uo pipefail
cd "$(dirname "$0")/wp-community-data"
fail=0
while read -r cmd; do
	if eval "${cmd/python3/python3 -I}" >/dev/null 2>&1; then echo "ok   $cmd"; else echo "FAIL $cmd"; fail=1; fi
done < <(grep -hoE 'python3 scripts/wpcd\.py [^`]*' SKILL.md references/recipes.md | sed 's/ *$//' | sort -u)
exit $fail
