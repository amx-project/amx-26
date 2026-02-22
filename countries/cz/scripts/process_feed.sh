#!/bin/bash
#
# process_feed.sh - Process a single dataset feed URL into GeoJSONSeq
# Usage: process_feed.sh <dataset_feed_url> <geojsonseq_dir>

set -e
set -o pipefail

DATASET_FEED_URL="$1"
GEOJSONSEQ_DIR="$2"

if [[ -z "$DATASET_FEED_URL" || -z "$GEOJSONSEQ_DIR" ]]; then
    echo "Error: dataset feed URL and output directory required" >&2
    exit 1
fi

extract_gml_url() {
    local feed_url="$1"
    curl -s --max-time 30 "$feed_url" 2>/dev/null | \
        yq -p=xml -o=json '.' 2>/dev/null | \
        jq -r '
            def normlinks(l): if (l|type)=="array" then l[] else l end;
            [
                (.feed.entry[]?.link? | normlinks(.) | .["+@href"]?),
                (.feed.link? | normlinks(.) | .["+@href"]?)
            ]
            | flatten
            | map(select(. != null))
            | map(select(test("\\.zip$|\\.gml$"; "i")))
            | .[0] // empty
        ' 2>/dev/null
}

GML_URL=$(extract_gml_url "$DATASET_FEED_URL" || echo "")
if [[ -z "$GML_URL" ]]; then
    exit 0
fi

BASE_NAME=$(basename "${GML_URL%%\?*}")
ID="${BASE_NAME%.*}"
OUTPUT_FILE="$GEOJSONSEQ_DIR/${ID}.geojsonseq"
TEMP_FILE="$GEOJSONSEQ_DIR/.${ID}.geojsonseq.tmp.$$"

if [[ -s "$OUTPUT_FILE" ]]; then
    echo "[skip] $BASE_NAME"
    exit 0
fi

echo "[run] $BASE_NAME"

OGR_SOURCE=""
if [[ "$GML_URL" =~ \.zip($|\?) ]]; then
    OGR_SOURCE="/vsizip//vsicurl/$GML_URL"
elif [[ "$GML_URL" =~ \.gml($|\?) ]]; then
    OGR_SOURCE="/vsicurl/$GML_URL"
else
    exit 0
fi

: > "$TEMP_FILE"
LAYER_NAMES=$(ogrinfo -ro -q "$OGR_SOURCE" 2>/dev/null | awk -F': ' '/^[0-9]+: /{print $2}')

if [[ -z "$LAYER_NAMES" ]]; then
    rm -f "$TEMP_FILE"
    echo "  ✗ No layers found"
    exit 0
fi

while IFS= read -r LAYER_NAME; do
    if [[ -z "$LAYER_NAME" ]]; then
        continue
    fi

    MINZOOM=14
    MAXZOOM=18
    case "$LAYER_NAME" in
        CadastralBoundary)
            MINZOOM=16
            MAXZOOM=18
            ;;
        CadastralZoning)
            MINZOOM=5
            MAXZOOM=13
            ;;
        CadastralParcel)
            MINZOOM=14
            MAXZOOM=18
            ;;
    esac

    if ! ogr2ogr -f GeoJSONSeq -lco COORDINATE_PRECISION=10 /vsistdout/ "$OGR_SOURCE" "$LAYER_NAME" 2>/dev/null | \
        jq -c --arg layer "$LAYER_NAME" --argjson minzoom "$MINZOOM" --argjson maxzoom "$MAXZOOM" \
            '.tippecanoe = {"layer": $layer, "minzoom": $minzoom, "maxzoom": $maxzoom} | .' \
            >> "$TEMP_FILE"; then
        echo "  ✗ Failed to convert layer: $LAYER_NAME"
    fi
done <<< "$LAYER_NAMES"

if [[ -s "$TEMP_FILE" ]]; then
    mv "$TEMP_FILE" "$OUTPUT_FILE"
    echo "  ✓ Wrote: $OUTPUT_FILE"
else
    rm -f "$TEMP_FILE"
    echo "  ✗ Failed to convert"
fi
