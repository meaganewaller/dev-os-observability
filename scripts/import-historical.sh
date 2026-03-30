#!/usr/bin/env bash
set -euo pipefail

# Import historical JSONL data into Loki
# Usage: ./scripts/import-historical.sh [file] [log_source]
# Example: ./scripts/import-historical.sh ~/.claude/dev-os-events.jsonl dev-os-events

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
FILE="${1:-$HOME/.claude/dev-os-events.jsonl}"
LOG_SOURCE="${2:-dev-os-events}"
BATCH_SIZE="${BATCH_SIZE:-500}"

if [[ ! -f "$FILE" ]]; then
    echo "Error: File not found: $FILE" >&2
    exit 1
fi

if ! command -v jq >/dev/null; then
    echo "Error: jq is required but not installed" >&2
    exit 1
fi

# Check Loki is reachable
if ! curl -sf "${LOKI_URL}/ready" >/dev/null 2>&1; then
    echo "Error: Loki not reachable at ${LOKI_URL}" >&2
    echo "Make sure docker compose is running" >&2
    exit 1
fi

total_lines=$(wc -l < "$FILE" | tr -d ' ')
echo "Importing from $FILE to Loki..."
echo "Log source: $LOG_SOURCE"
echo "Batch size: $BATCH_SIZE"
echo ""

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# Step 1: Filter valid JSON and prepend timestamp for sorting
echo "Filtering valid entries and extracting timestamps..."
jq -c -R 'try fromjson | select(type == "object") | [(.timestamp // .ts // "9999"), .]' "$FILE" 2>/dev/null | \
    sort -t'"' -k2 | \
    jq -c '.[1]' > "$tmpdir/sorted.jsonl"

valid_count=$(wc -l < "$tmpdir/sorted.jsonl" | tr -d ' ')
echo "Found $valid_count valid entries"

if [[ "$valid_count" -eq 0 ]]; then
    echo "No valid entries to import"
    exit 0
fi

# Step 2: Split into batches
split -l "$BATCH_SIZE" "$tmpdir/sorted.jsonl" "$tmpdir/batch_"

batch_files=("$tmpdir"/batch_*)
total_batches=${#batch_files[@]}
current_batch=0
total_imported=0
failed_batches=0

echo "Processing $total_batches batches..."
echo ""

for batch_file in "${batch_files[@]}"; do
    ((current_batch++)) || true

    # Convert batch to Loki format
    values=$(jq -c -s '
        [.[] |
            {
                ts: ((.timestamp // .ts // now) |
                    if type == "string" then
                        (sub("\\.[0-9]+Z?$"; "Z") | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime)
                    else . end),
                line: (. | tostring)
            } |
            ["\(.ts)000000000", .line]
        ]
    ' "$batch_file" 2>/dev/null) || {
        echo "Warning: Failed to parse batch $current_batch, skipping..." >&2
        ((failed_batches++)) || true
        continue
    }

    # Build and send payload
    payload=$(jq -n \
        --arg log_source "$LOG_SOURCE" \
        --argjson values "$values" \
        '{
            streams: [{
                stream: {
                    service_name: "devos",
                    log_source: $log_source
                },
                values: $values
            }]
        }')

    response=$(curl -sf -X POST "${LOKI_URL}/loki/api/v1/push" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1) && {
        lines_in_batch=$(wc -l < "$batch_file" | tr -d ' ')
        ((total_imported += lines_in_batch)) || true
    } || {
        echo ""
        echo "Warning: Failed to push batch $current_batch: $response" >&2
        ((failed_batches++)) || true
    }

    printf "\rBatch %d/%d - Imported: %d entries" "$current_batch" "$total_batches" "$total_imported"
done

echo ""
echo ""
echo "Done! Imported $total_imported of $valid_count entries."
[[ "$failed_batches" -gt 0 ]] && echo "Failed batches: $failed_batches"
exit 0
