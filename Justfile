# AMX-26: Cadastral Data to PMTiles
# Just commands for data conversion and deployment

set shell := ["zsh", "-cu"]

# Remote server configuration
REMOTE_USER := "pod"
REMOTE_HOST := "pod.local"
REMOTE_PATH := "/home/pod/x-24b/data"

# Countries (ISO 3166-1 alpha-2 codes)
COUNTRIES := "cz fr"

# Show all available commands
help:
	@just --list

# ============================================================================
# Core Commands
# ============================================================================

# Fetch ATOM feed from ČÚZK (saves as JSON locally)
fetch-feed COUNTRY:
	@bash scripts/fetch_feed.sh {{COUNTRY}}

# Show ATOM feed information
feed-info COUNTRY:
	#!/bin/zsh
	JSON_FILE="data/sources/{{COUNTRY}}/{{COUNTRY}}.json"
	if [[ ! -f "$JSON_FILE" ]]; then
		echo "Error: Feed JSON not found: $JSON_FILE"
		echo "Run: just fetch-feed {{COUNTRY}}"
		exit 1
	fi
	echo "Feed Information:"
	jq '.feed | {title: .title, updated: .updated, entries: (.entry | length)}' "$JSON_FILE"

# Download cadastral data for a country via ATOM feed or source
download COUNTRY:
	#!/bin/zsh
	if [[ ! "{{COUNTRIES}}" =~ "{{COUNTRY}}" ]]; then
		echo "Error: Unknown country '{{COUNTRY}}'"
		echo "Available: {{COUNTRIES}}"
		exit 1
	fi
	echo "Downloading {{COUNTRY}} cadastral data..."
	if [[ -f "countries/{{COUNTRY}}/scripts/download.sh" ]]; then
		bash countries/{{COUNTRY}}/scripts/download.sh
	else
		echo "✗ Download script not found: countries/{{COUNTRY}}/scripts/download.sh"
		exit 1
	fi

# Convert cadastral data to PMTiles for a country
convert COUNTRY:
	#!/bin/zsh
	if [[ ! "{{COUNTRIES}}" =~ "{{COUNTRY}}" ]]; then
		echo "Error: Unknown country '{{COUNTRY}}'"
		echo "Available: {{COUNTRIES}}"
		exit 1
	fi
	echo "Converting {{COUNTRY}} cadastral data to PMTiles..."
	cd countries/{{COUNTRY}}
	python scripts/convert.py

# Upload generated PMTiles file via rsync
upload COUNTRY:
	#!/bin/zsh
	if [[ ! "{{COUNTRIES}}" =~ "{{COUNTRY}}" ]]; then
		echo "Error: Unknown country '{{COUNTRY}}'"
		echo "Available: {{COUNTRIES}}"
		exit 1
	fi
	
	PMTILES="data/output/{{COUNTRY}}.pmtiles"
	if [[ ! -f "$PMTILES" ]]; then
		echo "Error: PMTiles file not found: $PMTILES"
		echo "Please run 'just convert {{COUNTRY}}' first"
		exit 1
	fi
	
	echo "Uploading {{COUNTRY}} PMTiles to {{REMOTE_USER}}@{{REMOTE_HOST}}:{{REMOTE_PATH}}..."
	rsync -av "$PMTILES" {{REMOTE_USER}}@{{REMOTE_HOST}}:{{REMOTE_PATH}}/
	echo "✓ Upload complete"

# Inspect generated GeoJSONSeq data before conversion to PMTiles
inspect-data COUNTRY:
	#!/bin/zsh
	GEOJSONSEQ_DIR="data/sources/{{COUNTRY}}/geojsonseq"
	GEOJSONSEQ_COMBINED="/tmp/amx-26-{{COUNTRY}}/combined.geojsonseq"
	
	if [[ -d "$GEOJSONSEQ_DIR" ]]; then
		FILE_COUNT=$(find "$GEOJSONSEQ_DIR" -type f -name "*.geojsonseq" | wc -l | tr -d ' ')
		if [[ "$FILE_COUNT" -gt 0 ]]; then
			echo "GeoJSONSeq Data Inspection"
			echo "Directory: $GEOJSONSEQ_DIR"
			echo ""
			echo "Statistics:"
			echo "  Files: $FILE_COUNT"
			echo "  Size: $(du -sh $GEOJSONSEQ_DIR | cut -f1)"
			echo ""
			SAMPLE_FILE=$(find "$GEOJSONSEQ_DIR" -type f -name "*.geojsonseq" | head -n 1)
			echo "Sample file: $SAMPLE_FILE"
			echo ""
			echo "First 3 entries (formatted):"
			head -3 "$SAMPLE_FILE" | jq '.' 2>/dev/null || head -3 "$SAMPLE_FILE"
			echo ""
			echo "Last 3 entries (formatted):"
			tail -3 "$SAMPLE_FILE" | jq '.' 2>/dev/null || tail -3 "$SAMPLE_FILE"
			exit 0
		fi
	fi
	
	if [[ ! -f "$GEOJSONSEQ_COMBINED" ]]; then
		echo "Error: GeoJSONSeq data not found"
		echo "Run: just download {{COUNTRY}}"
		exit 1
	fi
	
	echo "GeoJSONSeq Data Inspection"
	echo "File: $GEOJSONSEQ_COMBINED"
	echo ""
	echo "Statistics:"
	echo "  Lines: $(wc -l < $GEOJSONSEQ_COMBINED)"
	echo "  Size: $(du -h $GEOJSONSEQ_COMBINED | cut -f1)"
	echo ""
	echo "First 3 entries (formatted):"
	head -3 "$GEOJSONSEQ_COMBINED" | jq '.' 2>/dev/null || head -3 "$GEOJSONSEQ_COMBINED"
	echo ""
	echo "Last 3 entries (formatted):"
	tail -3 "$GEOJSONSEQ_COMBINED" | jq '.' 2>/dev/null || tail -3 "$GEOJSONSEQ_COMBINED"

# Full processing pipeline for a country (download → convert → upload)
process COUNTRY:
	#!/bin/zsh
	echo "Processing {{COUNTRY}}..."
	echo ""
	just download {{COUNTRY}}
	echo ""
	just convert {{COUNTRY}}
	echo ""
	just upload {{COUNTRY}}
	echo ""
	echo "✓ {{COUNTRY}} processing complete"

# Clean generated output for a country
clean COUNTRY:
	#!/bin/zsh
	if [[ ! "{{COUNTRIES}}" =~ "{{COUNTRY}}" ]]; then
		echo "Error: Unknown country '{{COUNTRY}}'"
		exit 1
	fi
	echo "Cleaning {{COUNTRY}} output..."
	rm -f data/output/{{COUNTRY}}.pmtiles
	rm -f data/sources/{{COUNTRY}}/geojsonseq/*.geojsonseq
	rm -f data/sources/{{COUNTRY}}/geojsonseq/*.tmp*
	echo "✓ Cleaned"

# Clean all country outputs
clean-all:
	#!/bin/zsh
	echo "Cleaning all outputs..."
	for country in {{COUNTRIES}}; do
		rm -f countries/$country/data/output/*.pmtiles
		rm -f data/sources/$country/geojsonseq/*.geojsonseq
		rm -f data/sources/$country/geojsonseq/*.tmp*
	done
	echo "✓ All cleaned"

# ============================================================================
# Utility Commands
# ============================================================================

# List countries and their status
status:
	#!/bin/zsh
	echo "Project Status: Cadastral Data to PMTiles Conversion"
	echo ""
	for country in {{COUNTRIES}}; do
		echo "📍 $country"
		if [[ -f "data/output/${country}.pmtiles" ]]; then
			size=$(du -h "data/output/${country}.pmtiles" | cut -f1)
			echo "   ✓ PMTiles: $size"
		else
			echo "   ○ PMTiles: Not generated"
		fi
	done

# Verify remote server connectivity
test-remote:
	#!/bin/zsh
	echo "Testing connection to {{REMOTE_USER}}@{{REMOTE_HOST}}..."
	ssh {{REMOTE_USER}}@{{REMOTE_HOST}} "ls -la {{REMOTE_PATH}} && echo '✓ Connected'" || echo "✗ Connection failed"

# ============================================================================
# Development Commands
# ============================================================================

# Initialize development environment
init:
	#!/bin/zsh
	echo "Initializing development environment..."
	echo "Required tools:"
	echo "  - Python 3.10+"
	echo "  - tippecanoe"
	echo "  - gdal/ogr tools (for GML processing)"
	echo ""
	echo "Optional: pip install -r requirements.txt (when created)"

# Check if all dependencies are available
check-deps:
	#!/bin/zsh
	echo "Checking dependencies..."
	which python3 > /dev/null && echo "✓ Python 3" || echo "✗ Python 3"
	which tippecanoe > /dev/null && echo "✓ tippecanoe" || echo "✗ tippecanoe (install: brew install tippecanoe)"
	which ogr2ogr > /dev/null && echo "✓ ogr2ogr" || echo "✗ ogr2ogr (install: brew install gdal)"
	which parallel > /dev/null && echo "✓ parallel" || echo "✗ parallel (install: brew install parallel)"

# Show configuration
config:
	#!/bin/zsh
	echo "Remote Configuration:"
	echo "  User: {{REMOTE_USER}}"
	echo "  Host: {{REMOTE_HOST}}"
	echo "  Path: {{REMOTE_PATH}}"
	echo ""
	echo "Countries:"
	for country in {{COUNTRIES}}; do
		echo "  - $country"
	done
