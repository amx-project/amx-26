# Czechia Cadastral Data to PMTiles

## Data Source

- **Provider**: Czech Office for Surveying, Mapping and Cadastre (ČÚZK)
- **Format**: Shapefile (distributed via ATOM feed)
- **Coverage**: Full Czech cadastre
- **License**: CC-BY
- **ATOM Feed**: https://atom.cuzk.cz/CP/CP.xml

## Data Acquisition

Cadastral data is distributed via ATOM feed and dataset feeds. Workflow:

```bash
# Step 1: Fetch ATOM feed from ČÚZK (saves as JSON locally)
just fetch-feed cz

# Step 2: Download GML files from dataset feeds (streaming to GeoJSONSeq)
just download cz

# Step 3: Inspect generated data before conversion (optional)
just inspect-data cz

# Step 4: Convert to PMTiles
just convert cz

# Step 5: Upload to pod server
just upload cz
```

**Pipeline Details**:
- `download` produces per-resource GeoJSONSeq files in `data/sources/cz/geojsonseq/`
- `inspect-data` shows statistics and sample entries (for verification)
- `convert` streams GeoJSONSeq files directly into tippecanoe (no combined temp file)

**Feed Structure**:
- Main ATOM feed: https://atom.cuzk.cz/CP/CP.xml (13,000+ dataset feeds)
- Each entry links to individual dataset feed with actual download URLs
- Data format: GML (OGC compliant, CC-BY licensed)

**Download outputs**:
- `data/sources/cz/cz.json` - Main ATOM feed (JSON)
- `data/sources/cz/dataset_feeds.txt` - List of dataset feed URLs
- `data/sources/cz/geojsonseq/*.geojsonseq` - Per-resource GeoJSONSeq outputs

## Conversion Process

```bash
# Full conversion pipeline
just convert cz

# Or manually:
cd /path/to/amx-26
python countries/cz/scripts/convert.py
```

## Output

Generated PMTiles file:
- **Location**: `data/output/cz.pmtiles`
- **Size**: 13GB (10,744,660 tiles, optimized)
- **Layers**:
  - CadastralBoundary: 62,484,714 features (LineString)
  - CadastralParcel: 22,074,158 features (Polygon)
  - CadastralZoning: 13,074 features (Polygon)
- **Zoom Levels**:
	- CadastralZoning: minzoom=5, maxzoom=13
	- CadastralParcel: minzoom=14, maxzoom=18
	- CadastralBoundary: minzoom=16, maxzoom=18
- **Average tile size**: 1.29KB
- **Max tile size**: 504KB
- **Attribution**: © ČÚZK (CC BY 4.0)

## Precision and Tile Settings

**Coordinate Precision**:
- Source GML: 1cm precision (0.01m in S-JTSK coordinate system EPSG:5514)
- Output GeoJSONSeq: 10 decimal places in WGS84 (0.01mm precision at 50°N latitude)
- Setting: `ogr2ogr -lco COORDINATE_PRECISION=10`

**Tippecanoe Settings**:
- Do not drop features: `--no-feature-limit`
- Increase per-tile size limit: `--maximum-tile-bytes 1000000`
- Temporary directory: `./tmp/amx-26-cz/tippecanoe-tmp` (avoids small system temp space)
- Progress display: Real-time processing progress shown during conversion
- Processing may take several hours for full dataset (44 GB, 84M+ features)
- Attribution: `--attribution "© ČÚZK"` (CC BY 4.0 license)

## Optimization

### Attribute Reduction - IMPLEMENTED

Based on web viewer usage analysis, attributes can be reduced significantly:

**CadastralBoundary** (6 attributes → 2 attributes):
- **Keep**: `estimatedAccuracy`, `estimatedAccuracy_uom` (precision metadata)
- **Remove**: `beginLifespanVersion`, `gml_id`, `localId`, `namespace`

**CadastralParcel** (9 attributes → 4 attributes):
- **Keep**: `label`, `areaValue`, `areaValue_uom`, `nationalCadastralReference` (used in web viewer)
- **Remove**: `gml_id`, `localId`, `namespace`, `beginLifespanVersion`, `pos`

**CadastralZoning** (13 attributes → 1 attribute):
- **Keep**: `label` (displayed in web viewer)
- **Remove**: All other INSPIRE metadata attributes

**Implementation**:
Filtering happens during GeoJSONSeq generation in `countries/cz/scripts/process_feed.sh`:
```bash
# Layer-specific property filter used by jq
FILTER_PROPS='{estimatedAccuracy, estimatedAccuracy_uom}'
# ... (set per layer)

ogr2ogr ... | jq -c ".properties |= $FILTER_PROPS | .tippecanoe = {layer: \"$LAYER_NAME\", minzoom: $MINZOOM, maxzoom: $MAXZOOM}"
```

**Results**:
- Total attributes reduced: 28 → 7 (75% reduction)
- File size reduction: 21GB → 13GB (about 38%)
- Average tile size reduction: 2.07KB → 1.29KB (about 37%)
- Faster tile loading in web viewer
- Source GeoJSONSeq files preserved for future regeneration

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

## Status

- [x] Identify INSPIRE data source (ATOM feed at atom.cuzk.cz)
- [x] Fetch ATOM feed with yq (just fetch-feed cz)
- [x] Process dataset feeds and extract GML URLs
- [x] Download GML files (streaming to GeoJSONSeq)
- [x] Convert GML → GeoJSONSeq with ogr2ogr
- [x] Implement PMTiles generation with tippecanoe
- [x] Test complete pipeline
- [x] Deploy web viewer (https://amx-project.github.io/amx-26/)
- [x] Analyze attributes with vt-optimizer-rs
- [x] Optimize PMTiles with attribute reduction
- [ ] Re-deploy optimized tiles

## Notes

(Add conversion notes, data quirks, or INSPIRE schema specifics as you discover them)
