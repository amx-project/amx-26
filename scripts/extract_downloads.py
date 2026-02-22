#!/usr/bin/env python3
"""
Query dataset feeds and extract download URLs

Fetches each dataset feed and extracts GML/Shapefile download URLs.
"""

import json
import sys
import urllib.request
import urllib.error
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_and_parse_feed(feed_url, timeout=30):
    """
    Fetch a dataset feed and extract download URLs
    
    Returns list of {format, size, url} dicts
    """
    try:
        with urllib.request.urlopen(feed_url, timeout=timeout) as response:
            xml_content = response.read().decode('utf-8')
            
        # Parse with yq via subprocess
        import subprocess
        proc = subprocess.run(
            ['yq', '-p=xml', '-o=json', '.feed.entry'],
            input=xml_content,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if proc.returncode != 0:
            return []
        
        entries = json.loads(proc.stdout)
        if not isinstance(entries, list):
            entries = [entries]
        
        urls = []
        for entry in entries:
            if 'link' not in entry:
                continue
            
            link = entry['link']
            href = link.get('+@href') or link.get('@href')
            file_type = link.get('+@type') or link.get('@type', '')
            length = link.get('+@length') or link.get('@length', '0')
            
            if href:
                # Determine format
                fmt = 'GML' if 'gml' in file_type.lower() else \
                      'Shapefile' if 'shapefile' in href.lower() or 'shp' in href.lower() else \
                      'Unknown'
                
                urls.append({
                    'url': href,
                    'format': fmt,
                    'size': length,
                    'type': file_type
                })
        
        return urls
    
    except Exception as e:
        print(f"Error fetching {feed_url}: {e}", file=sys.stderr)
        return []

def main():
    dataset_feeds_file = Path(__file__).parent.parent / "dataset_feeds.txt"
    
    if not dataset_feeds_file.exists():
        print(f"Error: {dataset_feeds_file} not found", file=sys.stderr)
        sys.exit(1)
    
    with open(dataset_feeds_file, 'r') as f:
        feed_urls = [line.strip() for line in f if line.strip()]
    
    print(f"Querying {len(feed_urls)} dataset feeds...")
    print(f"(Sampling first 100 for format detection)")
    
    all_downloads = []
    
    # Sample first 100 feeds to understand structure
    sample_urls = feed_urls[:100]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_and_parse_feed, url): url for url in sample_urls}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 10 == 0:
                print(f"  Processed {completed}/{len(sample_urls)}")
            
            try:
                urls = future.result()
                all_downloads.extend(urls)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
    
    print(f"\n✓ Found {len(all_downloads)} download URLs")
    
    # Group by format
    gml_urls = [d for d in all_downloads if d['format'] == 'GML']
    shapefile_urls = [d for d in all_downloads if d['format'] == 'Shapefile']
    unknown_urls = [d for d in all_downloads if d['format'] == 'Unknown']
    
    print(f"\nFormat breakdown:")
    print(f"  GML: {len(gml_urls)}")
    print(f"  Shapefile: {len(shapefile_urls)}")
    print(f"  Unknown: {len(unknown_urls)}")
    
    # Sample URLs by format
    print(f"\nSample GML URLs (first 3):")
    for url in gml_urls[:3]:
        print(f"  {url['url'][:80]}...")
    
    if shapefile_urls:
        print(f"\nSample Shapefile URLs (first 3):")
        for url in shapefile_urls[:3]:
            print(f"  {url['url'][:80]}...")
    
    # Save download URLs by format
    for fmt in ['GML', 'Shapefile']:
        urls = [d['url'] for d in all_downloads if d['format'] == fmt]
        if urls:
            output_file = Path(__file__).parent.parent / f"download_urls_{fmt.lower()}.txt"
            with open(output_file, 'w') as f:
                for url in urls:
                    f.write(f"{url}\n")
            print(f"\n✓ Saved {len(urls)} {fmt} URLs to: {output_file}")

if __name__ == '__main__':
    main()
