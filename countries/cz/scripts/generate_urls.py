#!/usr/bin/env python3
"""
Generate list of GML/Shapefile download URLs from ČÚZK ATOM feed.
Extracts dataset feed URLs from main feed, queries each, and generates bulk download URLs.
"""

import json
import sys
from pathlib import Path
from urllib.parse import urljoin
import urllib.request
import urllib.error

def load_main_feed(feed_json_path):
    """Load main ATOM feed from local JSON file."""
    try:
        with open(feed_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {feed_json_path} not found", file=sys.stderr)
        sys.exit(1)

def extract_dataset_feed_urls(main_feed):
    """Extract dataset feed URLs from main feed entries."""
    urls = []
    entries = main_feed.get('feed', {}).get('entry', [])
    
    if not isinstance(entries, list):
        entries = [entries]
    
    for entry in entries:
        links = entry.get('link', [])
        if not isinstance(links, list):
            links = [links]
        
        for link in links:
            if link.get('+@rel') == 'alternate' and 'datasetFeeds' in link.get('+@href', ''):
                urls.append(link['+@href'])
    
    return urls

def fetch_dataset_feed(dataset_feed_url, verbose=False):
    """Fetch and parse dataset feed from URL."""
    try:
        if verbose:
            print(f"Fetching: {dataset_feed_url}", file=sys.stderr)
        
        with urllib.request.urlopen(dataset_feed_url, timeout=30) as response:
            import xml.etree.ElementTree as ET
            root = ET.parse(response)
            
            # Convert XML to JSON-like structure
            ns = {
                'atom': 'http://www.w3.org/2005/Atom'
            }
            
            entries = []
            for entry_elem in root.findall('.//atom:entry', ns):
                entry = {}
                
                # Extract title
                title_elem = entry_elem.find('atom:title', ns)
                if title_elem is not None:
                    entry['title'] = title_elem.text
                
                # Extract link (file URI)
                link_elem = entry_elem.find('atom:link', ns)
                if link_elem is not None:
                    href = link_elem.get('href')
                    content_type = link_elem.get('type', '')
                    if href:
                        entry['href'] = href
                        entry['type'] = content_type
                
                if entry:
                    entries.append(entry)
            
            return entries
    
    except urllib.error.URLError as e:
        print(f"Error fetching {dataset_feed_url}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error parsing {dataset_feed_url}: {e}", file=sys.stderr)
        return []

def generate_download_urls(main_feed_json, output_file=None, verbose=False):
    """Generate list of GML/Shapefile download URLs."""
    
    # Load main feed
    main_feed = load_main_feed(main_feed_json)
    dataset_feed_urls = extract_dataset_feed_urls(main_feed)
    
    print(f"Found {len(dataset_feed_urls)} dataset feeds", file=sys.stderr)
    
    all_urls = []
    
    # Query each dataset feed
    for i, dataset_url in enumerate(dataset_feed_urls, 1):
        if verbose:
            print(f"[{i}/{len(dataset_feed_urls)}] Processing dataset feed...", file=sys.stderr)
        
        entries = fetch_dataset_feed(dataset_url, verbose=verbose)
        
        for entry in entries:
            url = entry.get('href')
            content_type = entry.get('type', '')
            
            # Filter for GML or Shapefile
            if url and ('gml' in content_type.lower() or 'shapefile' in content_type.lower() or 
                       url.endswith('.zip') or url.endswith('.gml')):
                all_urls.append({
                    'url': url,
                    'title': entry.get('title', ''),
                    'type': content_type
                })
    
    print(f"Found {len(all_urls)} download URLs", file=sys.stderr)
    
    # Output results
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in all_urls:
                f.write(item['url'] + '\n')
        print(f"URLs saved to: {output_file}", file=sys.stderr)
    else:
        for item in all_urls:
            print(item['url'])
    
    return all_urls

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate download URLs from ČÚZK ATOM feed')
    parser.add_argument('feed_json', help='Path to main ATOM feed JSON file')
    parser.add_argument('-o', '--output', help='Output file for URLs (default: stdout)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    generate_download_urls(args.feed_json, args.output, args.verbose)
