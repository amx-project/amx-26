#!/bin/bash
#
# fetch_feed.sh - Fetch ČÚZK ATOM feed and convert to JSON
# Stores the feed locally for subsequent processing
# Usage: scripts/fetch_feed.sh [country]

set -e

COUNTRY="${1:-cz}"
FEED_URL="https://atom.cuzk.cz/CP/CP.xml"
OUTPUT_DIR="data/sources/${COUNTRY}"
JSON_FILE="${OUTPUT_DIR}/cz.json"

echo "Fetching ČÚZK ATOM feed for ${COUNTRY}..."
echo "Feed URL: $FEED_URL"
echo "Output: $JSON_FILE"
echo ""

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Download and convert ATOM feed to JSON
# This may take a while due to ČÚZK server response time
echo "Downloading ATOM feed (this may take 1-2 minutes)..."
if curl -s --max-time 180 "$FEED_URL" | yq -p=xml -o=json '.' > "$JSON_FILE"; then
    echo "✓ Successfully downloaded and converted ATOM feed"
    
    # Show summary statistics
    echo ""
    echo "Feed Statistics:"
    jq '.feed | {title: .title, updated: .updated, source: "@ČÚZK"}' "$JSON_FILE"
    echo ""
    
    entry_count=$(jq '.feed.entry | length' "$JSON_FILE")
    echo "Total entries: $entry_count"
    echo "✓ Feed saved to: $JSON_FILE"
else
    echo "✗ Failed to download ATOM feed"
    exit 1
fi
