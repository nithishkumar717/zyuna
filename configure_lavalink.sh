#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Missing $ENV_FILE. Create it with your TOKEN and Lavalink password first." >&2
    exit 1
fi

TEMP_FILE="$(mktemp "$SCRIPT_DIR/.env.tmp.XXXXXX")"
trap 'rm -f "$TEMP_FILE"' EXIT

awk \
    -v host="nina.hidencloud.com" \
    -v port="24672" \
    -v secure="false" '
    {
        key = $0
        sub(/^[[:space:]]*/, "", key)
        sub(/[[:space:]]*=.*/, "", key)

        if (key == "LAVALINK_HOST") {
            if (!host_written) print "LAVALINK_HOST=" host
            host_written = 1
            next
        }
        if (key == "LAVALINK_PORT") {
            if (!port_written) print "LAVALINK_PORT=" port
            port_written = 1
            next
        }
        if (key == "LAVALINK_SECURE") {
            if (!secure_written) print "LAVALINK_SECURE=" secure
            secure_written = 1
            next
        }
        print
    }
    END {
        if (!host_written) print "LAVALINK_HOST=" host
        if (!port_written) print "LAVALINK_PORT=" port
        if (!secure_written) print "LAVALINK_SECURE=" secure
    }
' "$ENV_FILE" > "$TEMP_FILE"

chmod --reference="$ENV_FILE" "$TEMP_FILE" 2>/dev/null || chmod 600 "$TEMP_FILE"
mv -f "$TEMP_FILE" "$ENV_FILE"
trap - EXIT

echo "Lavalink settings updated: nina.hidencloud.com:24672 (HTTP)."
echo "Restart Zyuna to load the new settings."
