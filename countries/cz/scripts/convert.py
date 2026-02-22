#!/usr/bin/env python3
"""
Czechia Cadastral Data Conversion to PMTiles
Converts GeoJSONSeq (from download.sh) to PMTiles format.

Pipeline: download.sh generates combined.geojsonseq → tippecanoe → PMTiles
"""

import sys
import subprocess
from pathlib import Path

# Add common library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "lib"))

def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent.parent
    
    output_dir = root_dir / "data" / "output"
    output_file = output_dir / "cz.pmtiles"
    temp_dir = Path("/tmp/amx-26-cz")
    geojsonseq_dir = root_dir / "data" / "sources" / "cz" / "geojsonseq"
    geojsonseq_file = temp_dir / "combined.geojsonseq"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print("Czechia Cadastral Data Conversion Pipeline")
    print(f"Output: {output_file}")
    print()
    
    # Step 1: Check for GeoJSONSeq inputs
    print("Step 1: Checking for GeoJSONSeq data...")
    if not geojsonseq_dir.exists():
        print(f"Error: GeoJSONSeq directory not found: {geojsonseq_dir}")
        print("Please run: just download cz")
        return 1

    geojsonseq_files = sorted(geojsonseq_dir.glob("*.geojsonseq"))
    if not geojsonseq_files:
        print(f"Error: No GeoJSONSeq files found in: {geojsonseq_dir}")
        print("Please run: just download cz")
        return 1

    print(f"✓ Found GeoJSONSeq files: {len(geojsonseq_files)}")
    print(f"  Directory: {geojsonseq_dir}")
    print()

    # Step 2: Combine GeoJSONSeq files into a single stream
    print("Step 2: Combining GeoJSONSeq files...")
    with geojsonseq_file.open("wb") as combined:
        for path in geojsonseq_files:
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    combined.write(chunk)

    line_count = sum(1 for _ in open(geojsonseq_file, "rb"))
    size_mb = geojsonseq_file.stat().st_size / (1024 * 1024)
    print(f"✓ Combined GeoJSONSeq: {geojsonseq_file}")
    print(f"  Lines: {line_count}, Size: {size_mb:.1f} MB")
    print()
    
    # Step 3: Generate PMTiles from GeoJSONSeq
    print("Step 3: Generating PMTiles with tippecanoe...")
    try:
        result = subprocess.run(
            ['tippecanoe', '-z', '14', '-Z', '0', '-o', str(output_file), 
             '--drop-densest-as-needed', str(geojsonseq_file)],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            print(f"✓ Successfully generated: {output_file}")
            
            # Get file size
            size = output_file.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
            print()
            print("Pipeline complete!")
            print(f"Next: just upload cz")
            
            return 0
        else:
            print(f"✗ tippecanoe failed: {result.stderr}")
            return 1
    
    except subprocess.TimeoutExpired:
        print("✗ tippecanoe timeout (exceeded 10 minutes)")
        return 1
    except Exception as e:
        print(f"✗ Error running tippecanoe: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
