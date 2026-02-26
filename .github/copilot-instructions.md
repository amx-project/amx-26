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

- Generated in `./tmp/amx-26-*` (project-local temp directory)
- tippecanoe uses `./tmp/amx-26-cz/tippecanoe-tmp` for large conversions
- Automatically cleaned up by scripts
- Safe to delete manually if needed
- Excluded from git via .gitignore

## Web Viewer

Prototype web map viewer at `/web/` directory:

- **URL**: https://amx-project.github.io/amx-26/
- **Stack**: Vite + MapLibre GL JS + Protomaps basemaps (system fonts, no glyphs)
- **Build**: Single HTML file output to `docs/` for GitHub Pages
- **Justfile commands**:
  - `just site-install` - Install dependencies
  - `just site-dev` - Development server (with --host for network access)
  - `just site-build` - Production build to docs/
  - `just site-preview` - Preview production build (with --host)

**Key Features**:
- Czech cadastral layers (zoning z5-14, parcels z13-23, boundaries z13-23)
- Red outlines for all cadastral features, transparent fills
- Labels for zoning (z12-14) and parcels (z16.5-23)
- 3D terrain with hillshade (dark theme: white highlights, exaggeration 1.0)
- Layer control for visibility/opacity
- Parcel info on hover (label, area, nationalCadastralReference)
- Loading overlay during tile streaming
- Hash navigation for location sharing

**Data Sources**:
- `pmtiles://https://tunnel.optgeo.org/cz.pmtiles`
- Basemap: `https://tunnel.optgeo.org/martin/protomaps-basemap` (maxzoom 15)
- Terrain: `https://tunnel.optgeo.org/martin/mapterhorn` (maxzoom 12, terrarium encoding)
- Map maxZoom: 22 (with overzooming)

## Optimization Tools

### vt-optimizer-rs

[vt-optimizer-rs](https://github.com/unvt/vt-optimizer-rs) is used for vector tile inspection and optimization:

**Installation** (requires Rust):
```bash
git clone https://github.com/unvt/vt-optimizer-rs.git /tmp/vt-optimizer-rs
cd /tmp/vt-optimizer-rs
cargo build --release
cp target/release/vt-optimizer ~/.cargo/bin/
```

**Usage**:
```bash
# Inspect PMTiles structure
vt-optimizer inspect data/output/cz.pmtiles

# JSON output for programmatic analysis
vt-optimizer inspect data/output/cz.pmtiles --report-format json > report.json

# Optimize with style-based filtering (future)
vt-optimizer optimize input.pmtiles --output output.pmtiles --style style.json
```

**Current Czech PMTiles Stats** (as of optimization phase):
- Size: 13GB
- Tiles: 10,744,660 (10.1M entries)
- Layers: CadastralBoundary (62M features), CadastralParcel (22M features), CadastralZoning (13K features)
- Average tile size: 1.29KB
- Max tile size: 504KB
- Compression: gzip

**vt-optimizer report excerpt** (from `tmp/cz_report.json`):
```json
{
  "overall": {
    "tile_count": 10744660,
    "total_bytes": 14158698421,
    "avg_bytes": 1317,
    "max_bytes": 516523
  },
  "vector_layers": [
    {
      "id": "CadastralBoundary",
      "fields": {
        "estimatedAccuracy": "Number",
        "estimatedAccuracy_uom": "String"
      }
    },
    {
      "id": "CadastralParcel",
      "fields": {
        "areaValue": "Number",
        "areaValue_uom": "String",
        "label": "Mixed",
        "nationalCadastralReference": "String"
      }
    },
    {
      "id": "CadastralZoning",
      "fields": {
        "label": "String"
      }
    }
  ]
}
```

### Attribute Reduction Strategy

Web viewer analysis shows most attributes are unused. Reduction targets:

- **CadastralBoundary**: Keep `estimatedAccuracy`, `estimatedAccuracy_uom` only (precision metadata)
- **CadastralParcel**: Keep `label`, `areaValue`, `areaValue_uom`, `nationalCadastralReference`
- **CadastralZoning**: Keep `label` only

**Implementation**: Filter attributes during GeoJSONSeq generation via jq in `countries/cz/scripts/process_feed.sh` (preserves source data while reducing output).

**Goals**:
- Reduce file size by 30-50%
- Maintain all display/interaction functionality
- Preserve source data for future regeneration

## Known Limitations & TODOs

1. **ČÚZK Network**: Very slow (1-2 min to fetch full ATOM feed)
   - Solution: Cache ATOM feed locally (current approach)

2. **Dataset Scale**: 13,074 dataset feeds for Czechia
   - Solution: Process in batches, implement parallel downloads

3. **GML Parsing**: Complex INSPIRE schemas
   - Solution: Use ogr2ogr for robust handling; test with sample regions first

4. **PMTiles Size**: Full Czech cadastre is 13GB after attribute reduction (was 21GB)
  - Solution: Attribute reduction via jq filtering in process_feed.sh
   - Future: vt-optimizer-rs style-based layer filtering

## Reference Materials

- [INSPIRE Directive](https://inspire.ec.europa.eu/)
- [ČÚZK Cadastral Data](https://geoportal.cuzk.gov.cz/)
- [PMTiles Format](https://protomaps.com/docs/pmtiles/)
- [Matterhorn Project](https://matterhorn.app/) (inspiration for approach)

## Maintainer Notes

- **Current Focus**: Re-deploy optimized PMTiles for Czechia
- **Completed**: End-to-end pipeline (download → convert → PMTiles), web viewer deployment, attribute reduction implementation, optimized PMTiles generation
- **In Progress**: Final verification and deployment
- **Next Phase**: Re-deploy optimized tiles, then scale to France
- **Long-term**: Automated CI/CD pipeline (currently manual via Justfile)

---

**Last Updated**: February 27, 2026
