# France Cadastral Data to PMTiles

## Data Source

- **Provider**: French Cadastre (cadastre.gouv.fr or INSPIRE)
- **Format**: To be determined
- **Coverage**: Full French cadastre
- **License**: Check French cadastre terms

## Data Acquisition

Place raw cadastral data in `data/sources/fr/` directory (global location):

```bash
data/sources/fr/
├── (data files to be determined)
└── ...
```

## Conversion Process

```bash
# Full conversion pipeline
just convert fr

# Or manually:
cd /path/to/amx-26
python countries/fr/scripts/convert.py
```

## Output

Generated PMTiles file:
- **Location**: `data/output/fr.pmtiles`
- **Size**: (to be determined)
- **Zoom Levels**: (to be configured)

## Status

- [ ] Identify French cadastral INSPIRE data source
- [ ] Determine data format
- [ ] Download sample data
- [ ] Implement conversion script
- [ ] Test PMTiles generation
- [ ] Optimize for performance

## Notes

(Add conversion notes and implementation details as you progress)
