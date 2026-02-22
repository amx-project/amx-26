"""
Architecture and design patterns for AMX-26 project
"""

# Data Pipeline Architecture
# ============================================================================
#
# INSPIRE Sources (Country-specific)
#   │
#   └─→ Raw Data (GML/WFS)
#       │
#       ├─→ Parse & Normalize (country/scripts/convert.py)
#       │   └─→ Extract cadastral features
#       │
#       ├─→ Validate (common/lib)
#       │   └─→ Check INSPIRE compliance
#       │
#       ├─→ Tile Generation (tippecanoe)
#       │   └─→ Generate vector tiles
#       │
#       └─→ PMTiles Archive (common/lib)
#           └─→ countries/{country}/data/output/{country}-cadastre.pmtiles
#
# Deployment
#   │
#   └─→ rsync to pod@pod.local:/home/pod/x-24b/data/
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
# Phase 1: Czechia (First Country)
#   - Identify INSPIRE data source
#   - Implement basic GML→PMTiles pipeline
#   - Test rsync deployment
#   - Document process
#
# Phase 2: France
#   - Adapt pipeline to French data format
#   - Reuse common utilities
#   - Verify cross-country approach
#
# Phase 3: Scale
#   - Add more countries
#   - Optimize conversion performance
#   - Enhance metadata handling
#
