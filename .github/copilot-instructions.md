# AMX-26 Development Guidelines for AI Assistants

## Project Overview

**AMX-26** converts open cadastral data from European countries (within the INSPIRE framework) into PMTiles format for efficient geospatial information access.

- **Tagline**: Openness lowers the cost of trust. PMTiles lowers the cost of distribution.
- **Phase**: Prototype implementation
- **Current Countries**: Czech Republic (cz), France (fr)
- **Deployment**: rsync-based file distribution to pod@pod.local

## Core Architecture

### Data Pipeline

```
ATOM Feed (ČÚZK) 
  ↓ [just fetch-feed cz]
cz.json (in data/sources/cz/)
  ↓ [parse dataset feeds]
GML files (download)
  ↓ [ogr2ogr → GeoJSONSeq]
GeoJSONSeq
  ↓ [tippecanoe]
PMTiles (data/output/cz.pmtiles)
  ↓ [just upload cz]
pod@pod.local:/home/pod/x-24b/data/
```

### Directory Structure

```
amx-26/
├── countries/          # Per-country pipelines (cz, fr)
│   └── {code}/
│       ├── scripts/    # Country-specific scripts
│       │   ├── convert.py       # Main conversion pipeline
│       │   ├── download.sh      # Data download orchestration
│       │   └── generate_urls.py # URL extraction from feeds
│       └── README.md   # Country-specific documentation
├── data/
│   ├── sources/{code}/ # Downloaded GML/Shapefile & ATOM feeds
│   └── output/         # Generated PMTiles files
├── common/
│   ├── lib/           # Reusable Python libraries
│   └── scripts/       # Global utility scripts
├── scripts/           # Top-level scripts (e.g., fetch_feed.sh)
├── Justfile           # Task orchestration (MINIMAL logic)
└── .github/
    └── copilot-instructions.md (this file)
```

## Key Design Principles

### 1. Minimize Justfile Complexity
- **Justfile**: Task orchestration only (what to run)
- **Scripts**: Actual logic (in bash/python, how to run)
- **Rationale**: Avoid syntax conflicts between Just and script languages

### 2. Prototype Over Perfection
- Focus on working implementations
- Iterate based on real data
- Don't over-engineer early

### 3. Modular Country Handling
- Each country has independent `scripts/` directory
- Shared logic in `common/lib/`
- Easy to add new countries

### 4. Data-Driven Approach
- Use local JSON files (cz.json) instead of repeated network calls
- ATOM feeds fetched once: `just fetch-feed cz`
- Subsequent processing uses cached JSON

## Common Tasks & Commands

### Fetching & Processing Data

```bash
# Step 1: Fetch ATOM feed (stores as cz.json locally)
just fetch-feed cz

# Step 2: Display feed info
just feed-info cz

# Step 3: Download GML files
just download cz

# Step 4: Convert to PMTiles
just convert cz

# Step 5: Upload to remote
just upload cz

# Or: Full pipeline
just process cz
```

### Tools Used

- **yq** (YAML/XML query): Parse ATOM feeds
- **ogr2ogr** (GDAL): Convert GML → GeoJSONSeq
- **tippecanoe**: Generate PMTiles from GeoJSON
- **rsync**: Distribute files to pod server
- **just**: Task runner (simpler than Make)

### Environment Prerequisites

```bash
brew install yq tippecanoe gdal just
```

## Development Guidelines

### When Adding Features

1. **Check if it fits Justfile**: Only if it's a simple one-liner or basic orchestration
2. **Otherwise**: Create/update a script in `scripts/` or `countries/{code}/scripts/`
3. **Update Documentation**: Keep README.md and this file in sync

### Code Style

- **Python**: Type hints, docstrings, error handling
- **Bash**: Error checking (`set -e`, check return codes)
- **Comments**: Explain "why", not "what"

### Handling Network Issues

- ČÚZK servers are slow; use `just fetch-feed cz` to cache JSON locally
- Re-run `just fetch-feed cz` to refresh (overwrites cz.json)
- Implement retries and timeouts in scripts

## Testing & Debugging

### Minimal Testing Setup

```bash
# Test a script in isolation
python countries/cz/scripts/convert.py

# Check tool availability
just check-deps

# View current project status
just status
```

### Temporary Files

- Generated in `/tmp/amx-26-*`
- Automatically cleaned up by scripts
- Safe to delete manually if needed

## Known Limitations & TODOs

1. **ČÚZK Network**: Very slow (1-2 min to fetch full ATOM feed)
   - Solution: Cache ATOM feed locally (current approach)

2. **Dataset Scale**: 13,074 dataset feeds for Czechia
   - Solution: Process in batches, implement parallel downloads

3. **GML Parsing**: Complex INSPIRE schemas
   - Solution: Use ogr2ogr for robust handling; test with sample regions first

4. **PMTiles Size**: Full Czech cadastre will be very large (~500MB+)
   - Solution: Consider regional splits or zoom level optimization

## Reference Materials

- [INSPIRE Directive](https://inspire.ec.europa.eu/)
- [ČÚZK Cadastral Data](https://geoportal.cuzk.gov.cz/)
- [PMTiles Format](https://protomaps.com/docs/pmtiles/)
- [Matterhorn Project](https://matterhorn.app/) (inspiration for approach)

## Maintainer Notes

- **Current Focus**: Getting Czechia prototype working end-to-end
- **Next Phase**: Scale to France and additional countries
- **Long-term**: Automated CI/CD pipeline (currently manual via Justfile)

---

**Last Updated**: February 22, 2026
