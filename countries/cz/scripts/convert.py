#!/usr/bin/env python3
"""
Czechia Cadastral Data Conversion to PMTiles
Converts GeoJSONSeq (from download.sh) to PMTiles format.

Pipeline: download.sh generates combined.geojsonseq → tippecanoe → PMTiles
"""

import sys
import subprocess
import os
from pathlib import Path

# Add common library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "lib"))

def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent.parent
    
    output_dir = root_dir / "data" / "output"
    output_file = output_dir / "cz.pmtiles"
    temp_dir = root_dir / "tmp" / "amx-26-cz"
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
    
    # Calculate total input size
    total_size = sum(p.stat().st_size for p in geojsonseq_files)
    total_size_gb = total_size / (1024**3)
    print(f"  Total input size: {total_size_gb:.2f} GB")
    print()

    # Step 2: Stream GeoJSONSeq files to tippecanoe via shell pipe
    # Use ls|grep|xargs to avoid wildcard length limits.
    print("Step 2: Streaming GeoJSONSeq to tippecanoe...")
    print(f"  Processing {len(geojsonseq_files)} files (this may take 30-60 minutes)...")
    print(f"  tippecanoe progress will be shown below:")
    print()
    
    # Set tippecanoe temp directory to avoid small system temp space
    tippecanoe_temp = temp_dir / "tippecanoe-tmp"
    tippecanoe_temp.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = (
            f'ls -1 "{geojsonseq_dir}" | '
            r'grep -E "\.geojsonseq$" | '
            f'sed "s#^#{geojsonseq_dir}/#" | '
            f'xargs cat | tippecanoe -f -z 18 -Z 0 -o "{output_file}" '
            f'--attribution "© ČÚZK" --no-feature-limit --maximum-tile-bytes 1000000'
        )
        
        env = os.environ.copy()
        env["TMPDIR"] = str(tippecanoe_temp)
        
        # Run with stderr visible for progress reporting
        # No timeout - let tippecanoe complete regardless of duration
        result = subprocess.run(
            cmd,
            shell=True,
            stderr=None,  # Show tippecanoe's progress output
            stdout=subprocess.PIPE,
            text=True,
            cwd=root_dir,
            env=env
        )
        
        if result.returncode == 0:
            print()
            print(f"✓ Successfully generated: {output_file}")
            
            # Get file size
            size = output_file.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"  Files processed: {len(geojsonseq_files)}")
            print(f"  Size: {size_mb:.1f} MB")
            print()
            print("Pipeline complete!")
            print(f"Next: just upload cz")
            
            return 0
        else:
            print()
            print(f"✗ tippecanoe failed (exit code {result.returncode})")
            print("  Check the error messages above for details")
            return 1
    
    except Exception as e:
        print(f"✗ Error running tippecanoe: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
