#!/bin/bash
#
# download.sh - Download Czech cadastral data from ČÚZK ATOM feed
# Processes cz.json to extract and download GML/Shapefile data via streaming pipeline
# Requires: cz.json (generate with: just fetch-feed cz)
# Note: Runs from project root (via Justfile)

set -e
set -o pipefail

# Paths are relative to project root where Justfile runs
OUTPUT_DIR="data/sources/cz"
JSON_FILE="${OUTPUT_DIR}/cz.json"
TEMP_DIR="/tmp/amx-26-cz"
GEOJSONSEQ_DIR="${OUTPUT_DIR}/geojsonseq"
SAMPLE_SIZE=${SAMPLE_SIZE:-10}
PARALLEL_JOBS=${PARALLEL_JOBS:-2}

echo "Czech Cadastral Data Download"
echo "Output directory: $OUTPUT_DIR"
echo "Temp directory: $TEMP_DIR"
echo "GeoJSONSeq directory: $GEOJSONSEQ_DIR"
echo "Parallel jobs: $PARALLEL_JOBS"
echo "Sample size: $SAMPLE_SIZE"
echo ""

# Check if JSON file exists
if [[ ! -f "$JSON_FILE" ]]; then
    echo "Error: ATOM feed JSON not found: $JSON_FILE"
    echo "Please run: just fetch-feed cz"
    exit 1
fi

# Create temp directory
mkdir -p "$TEMP_DIR"

# Create GeoJSONSeq output directory
mkdir -p "$GEOJSONSEQ_DIR"

# Extract dataset feed URLs
echo "Extracting dataset feed URLs..."
jq -r '.feed.entry[].link[] | select(."+@rel" == "alternate" and ."+@type" == "application/atom+xml") | ."+@href"' "$JSON_FILE" > "${OUTPUT_DIR}/dataset_feeds.txt"

FEED_COUNT=$(wc -l < "${OUTPUT_DIR}/dataset_feeds.txt")
echo "✓ Found $FEED_COUNT dataset feeds"
echo ""

# Process dataset feeds to extract and download GML files
# Pipeline: dataset feed URL → curl → yq to JSON → extract GML URL → curl → ogr2ogr → GeoJSONSeq
echo "Processing dataset feeds and downloading GML (streaming to GeoJSONSeq)..."

if ! command -v parallel >/dev/null 2>&1; then
    echo "Error: GNU parallel not found (install: brew install parallel)"
    exit 1
fi

PROCESS_SCRIPT="countries/cz/scripts/process_feed.sh"
if [[ ! -x "$PROCESS_SCRIPT" ]]; then
    echo "Error: Missing executable: $PROCESS_SCRIPT"
    exit 1
fi

if [[ "$SAMPLE_SIZE" -gt 0 ]]; then
    head -n "$SAMPLE_SIZE" "${OUTPUT_DIR}/dataset_feeds.txt" | \
        parallel --no-notice --line-buffer -j "$PARALLEL_JOBS" "$PROCESS_SCRIPT" {} "$GEOJSONSEQ_DIR"
else
    cat "${OUTPUT_DIR}/dataset_feeds.txt" | \
        parallel --no-notice --line-buffer -j "$PARALLEL_JOBS" "$PROCESS_SCRIPT" {} "$GEOJSONSEQ_DIR"
fi

echo ""
FILE_COUNT=$(find "$GEOJSONSEQ_DIR" -type f -name "*.geojsonseq" | wc -l | tr -d ' ')
DIR_SIZE=$(du -sh "$GEOJSONSEQ_DIR" | cut -f1)
echo "✓ GeoJSONSeq files ready: $GEOJSONSEQ_DIR"
echo "  Files: $FILE_COUNT"
echo "  Size: $DIR_SIZE"

