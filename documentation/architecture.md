"""
Architecture and design patterns for AMX-26 project
"""

# Data Pipeline Architecture
# ============================================================================
#
# INSPIRE Sources (Country-specific)
#   |
#   +-+ Raw Data (GML/WFS)
#       |
#       +-+ Extract & Convert (countries/{country}/scripts/download.sh)
#       |   +-+ GeoJSONSeq per resource (data/sources/{country}/geojsonseq)
#       |
#       +-+ Validate (common/lib)
#       |   +-+ Check INSPIRE compliance
#       |
#       +-+ Tile Generation (tippecanoe)
#       |   +-+ Stream GeoJSONSeq into PMTiles
#       |
#       +-+ PMTiles Archive (data/output/{country}.pmtiles)
#
# Deployment
#   |
#   +-+ rsync to pod@pod.local:/home/pod/x-24b/data/
#

# Design Principles
# ============================================================================
#
# 1. Modularity: Each country has independent conversion scripts
# 2. Reusability: Common logic in common/lib/
# 3. Simplicity: Plain Python scripts, no complex frameworks
# 4. Transparency: All steps logged and documented
# 5. Prototyping: Fast iteration over perfection
#

# Implementation Strategy
# ============================================================================
#
# Phase 1: Czechia (First Country) - COMPLETED
#   - Identify INSPIRE data source ✓
#   - Implement basic GML->PMTiles pipeline ✓
#   - Test rsync deployment ✓
#   - Document process ✓
#   - Build web viewer ✓
#   - Deploy to GitHub Pages ✓
#
# Phase 2: Optimization (Current)
#   - Analyze tile structure with vt-optimizer-rs ✓
#   - Implement attribute reduction strategy
#   - Re-generate optimized PMTiles
#   - Measure size reduction and performance gains
#
# Phase 3: France
#   - Adapt pipeline to French data format
#   - Reuse common utilities
#   - Verify cross-country approach
#   - Apply optimization learnings from Czech experience
#
# Phase 4: Scale
#   - Add more countries
#   - Optimize conversion performance
#   - Enhance metadata handling
#
# Web Viewer Architecture
# ============================================================================
#
# Frontend Stack:
#   - Vite 6.1.0 (build tool with vite-plugin-singlefile)
#   - MapLibre GL JS 5.14.0 (no globe projection)
#   - Protomaps basemaps 5.7.0 (system fonts, no glyphs)
#   - maplibre-gl-layer-control 0.14.0
#   - PMTiles 3.0.0 protocol
#
# Data Sources:
#   - Cadastral: pmtiles://https://tunnel.optgeo.org/cz.pmtiles
#   - Basemap: https://tunnel.optgeo.org/martin/protomaps-basemap (maxzoom 15)
#   - Terrain: https://tunnel.optgeo.org/martin/mapterhorn (terrarium, maxzoom 12)
#
# Layer Configuration:
#   - CadastralZoning: z5-14 (fills + outlines + labels z12-14)
#   - CadastralParcel: z13-23 (fills + outlines + labels z16.5-23)
#   - CadastralBoundary: z13-23 (lines only)
#   - All cadastral lines: #ff4747 (red)
#   - All cadastral fills: transparent
#   - Labels: red text (#ff4747) with dark halo (#0b0d12)
#
# Terrain & Hillshade:
#   - 3D terrain with exaggeration: 1.0
#   - Hillshade: white highlights (0.15 opacity), dark shadows (0.35 opacity)
#   - Accent color: warm brown (rgba(180,140,100,0.2))
#   - Illumination: 315° (northwest)
#   - Positioned above basemap, below cadastral layers
#
# UI Features:
#   - Status bar (left-top): Shows parcel info on hover
#   - Layer control (bottom-left): Toggle visibility/opacity
#   - Navigation control (bottom-left)
#   - Loading overlay: Blur + message during tile streaming
#   - Popup: Label + area + national reference on click
#   - Hash navigation: URL-based location sharing
#
# Build & Deployment:
#   - Output: Single HTML file (docs/index.html) with inlined JS/CSS
#   - GitHub Pages: https://amx-project.github.io/amx-26/
#   - Base path: /amx-26/
#   - Max zoom: 22 (with overzooming)
#
