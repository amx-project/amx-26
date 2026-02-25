# AMX-26: Cadastral Data to PMTiles

**Tagline**: *Openness lowers the cost of trust. PMTiles lowers the cost of distribution.*

A collaborative initiative to convert open INSPIRE cadastral data from European countries into PMTiles format, enabling efficient and fast geospatial information access.

## Vision

This project transforms open cadastral data within the European INSPIRE framework into PMTiles, improving accessibility and performance for geospatial applications. Similar to Mapterhorn's approach for elevation data, we focus on cadastral data, with country-level PMTiles files served efficiently via rsync.

## Project Status

**Phase**: Prototype Implementation

- **Priority Countries**: Czechia (first), France (next)
- **Approach**: Single monorepo with per-country data pipelines
- **Deployment**: rsync-based file hosting to pod@pod.local

## Repository Structure

```
amx-26/
├── countries/
│   ├── cz/
│   │   ├── README.md
│   │   ├── data/
│   │   │   ├── source/      # Raw INSPIRE data (local fallback)
│   │   │   └── output/      # (deprecated - use data/output)
│   │   └── scripts/
│   │       └── convert.py   # Conversion pipeline
│   └── fr/
│       ├── README.md
│       ├── data/
│       │   ├── source/
│       │   └── output/
│       └── scripts/
│           └── convert.py
├── data/
│   ├── sources/
│   │   ├── cz/              # Czechia cadastral source data
│   │   │   └── geojsonseq/  # Per-resource GeoJSONSeq outputs
│   │   └── fr/              # France cadastral source data
│   └── output/              # Generated PMTiles files
│       ├── cz.pmtiles
│       └── fr.pmtiles
├── common/
│   ├── scripts/             # Shared conversion utilities
│   └── lib/                 # Reusable Python modules
├── docs/
│   ├── architecture.md
│   └── data-format.md
└── Justfile
```

## Quick Start

### Prerequisites

- Python 3.10+
- [tippecanoe](https://github.com/mapbox/tippecanoe) (for vector tile generation)
- `just` (task runner, [install here](https://github.com/casey/just))
- `yq` (YAML/XML query tool, `brew install yq`) - for parsing ATOM feeds
- `xq` (XML query tool, `brew install xq`) - alternative/companion to yq
- `parallel` (GNU parallel, `brew install parallel`) - for download concurrency

### Workflow

```bash
# List all available commands
just --list

# Step 1: Fetch ATOM feed (stores JSON locally)
just fetch-feed cz

# Step 2: Show feed information
just feed-info cz

# Step 3: Download GML files from dataset feeds
just download cz

# Optional: control download concurrency
# SAMPLE_SIZE=-1 processes all feeds (0 also works), PARALLEL_JOBS controls parallelism
SAMPLE_SIZE=-1 PARALLEL_JOBS=2 just download cz

# Step 4: Convert to PMTiles
just convert cz

# Step 5: Upload to remote host
just upload cz

# Or: Full pipeline (all steps)
just process cz
```

## Country Pipelines

### Czechia (cz)
- **Status**: INSPIRE data source identified
- **Format**: Shapefile (distributed via ATOM feed)
- **Source**: [ČÚZK ATOM Feed](https://atom.cuzk.cz/CP/CP.xml)
- **License**: CC-BY
- **Target**: `cz.pmtiles`

**GeoJSONSeq Outputs**:
- Per-resource files in `data/sources/cz/geojsonseq/*.geojsonseq`
- Files are written atomically (temporary name, then rename)
- Existing files are skipped on subsequent runs for faster rebuilds
- Layer-based `tippecanoe.minzoom/maxzoom` metadata is added during download
- Conversion streams per-resource GeoJSONSeq directly to tippecanoe (no combined temp file)

**Data Acquisition Strategy**:
```bash
# ATOM feed parsing with yq/xq
yq -p xml '.feed.entry[] | select(.id == "...") | .link.@href' https://atom.cuzk.cz/CP/CP.xml

# Automated download via download.sh script
just download cz
```

**Zoom Level Strategy**:
- **CadastralZoning**: minzoom=5, maxzoom=13 (broad coverage, lightweight data)
- **CadastralParcel**: minzoom=14, maxzoom=18 (transitions at z14 from CadastralZoning)
- **CadastralBoundary**: minzoom=16, maxzoom=18 (high precision detail)
- tippecanoe maxzoom: 18

This ensures continuous coverage across all zoom levels without gaps where features disappear.

**Coordinate Precision**:
- Source GML: 1cm precision (0.01m in S-JTSK coordinate system EPSG:5514)
- Output GeoJSONSeq: 10 decimal places in WGS84 (0.01mm precision at 50°N latitude)
- Setting: `ogr2ogr -lco COORDINATE_PRECISION=10`
- Rationale: Future-proof for millimeter-precision data while preserving original centimeter precision

**Verification**:
Zoom level distribution verified using tippecanoe-decode on actual tiles:
- z5: CadastralZoning only (broad coverage)
- z10: CadastralZoning only (continues until maxzoom=13)
- z14: CadastralParcel appears (transitions from CadastralZoning)
- z16: CadastralBoundary added (high-detail boundaries)
- z18: CadastralParcel + CadastralBoundary (maximum detail)

Note: PMTiles metadata shows global minzoom/maxzoom (0-18) for all layers, but actual tiles contain only the appropriate layers per zoom level as configured in GeoJSONSeq features.

**Tippecanoe Settings**:
- Do not drop features: `--no-feature-limit`
- Increase per-tile size limit: `--maximum-tile-bytes 1000000`
- Temporary directory: `./tmp/amx-26-cz/tippecanoe-tmp` (avoids small system temp space)
- Progress display: Real-time processing progress shown during conversion
- Processing may take several hours for full dataset (44 GB, 84M+ features)

### France (fr)
- Status: Planned
- Format: To be determined
- Target: `fr.pmtiles`

## Development

### Adding a New Country

1. Create a new directory: `countries/{country}/`
2. Add country-specific `README.md` with data source details
3. Create `scripts/convert.py` tailored to your data format
4. Update `Justfile` with country-specific tasks

### Shared Libraries

Place reusable conversion logic in `common/lib/`. For example:
- INSPIRE data parsing
- PMTiles encoding utilities
- Metadata handling

## Deployment

### Upload to Pod Server

Files are hosted via rsync to a remote pod server:

```bash
just upload cz
# Executes: rsync -av data/output/cz.pmtiles pod@pod.local:/home/pod/x-24b/data/
```

### Tile Access URLs

Once deployed, Czech cadastral tiles are available at:

- **PMTiles (direct)**: https://tunnel.optgeo.org/cz.pmtiles
- **TileJSON metadata**: https://tunnel.optgeo.org/martin/cz
- **XYZ tiles**: https://tunnel.optgeo.org/martin/cz/{z}/{x}/{y}

The `martin` server provides TileJSON compatibility for web mapping libraries (Leaflet, Mapbox GL, etc.)

## References

- [INSPIRE Directive](https://inspire.ec.europa.eu/)
- [PMTiles Specification](https://protomaps.com/docs/pmtiles/)
- [Matterhorn Project](https://matterhorn.app/) (elevation data)
- [amx-project](https://github.com/unvt/amx-project)
- [x-24b](https://github.com/unvt/x-24b)

**Data Sources**:
- [ČÚZK Cadastral Data ATOM Feed](https://atom.cuzk.cz/CP/CP.xml) - Czech cadastral data

**Tools**:
- [yq](https://github.com/mikefarah/yq) - YAML/XML query tool (`brew install yq`)
- [xq](https://github.com/sibprogrammer/xq) - XML query tool (`brew install xq`)

## License

See [LICENSE](LICENSE)
