#!/usr/bin/env python3
"""
Extract bulk download URLs from ČÚZK ATOM feed

Extracts dataset feed URLs from cz.json, then queries each feed
to find GML/Shapefile download URLs.
"""

import json
import sys
from pathlib import Path

def extract_dataset_feed_urls(feed_json):
    """
    Extract dataset feed URLs from main ATOM feed JSON
    
    Returns list of (entry_id, dataset_feed_url) tuples
    """
    dataset_feeds = []
    
    if 'feed' not in feed_json or 'entry' not in feed_json['feed']:
        print("Error: Invalid feed structure", file=sys.stderr)
        return []
    
    for entry in feed_json['feed']['entry']:
        entry_id = entry.get('id', 'unknown')
        
        # Find the "dataset feed" link
        if 'link' not in entry:
            continue
            
        links = entry['link']
        if not isinstance(links, list):
            links = [links]
        
        for link in links:
            if link.get('+@title') == 'dataset feed':
                dataset_url = link.get('+@href')
                if dataset_url:
                    dataset_feeds.append({
                        'entry_id': entry_id,
                        'title': entry.get('title', 'unknown'),
                        'dataset_feed_url': dataset_url
                    })
                break
    
    return dataset_feeds

def main():
    cz_json_path = Path(__file__).parent.parent / "cz.json"
    
    print(f"Loading: {cz_json_path}")
    with open(cz_json_path, 'r', encoding='utf-8') as f:
        feed_json = json.load(f)
    
    dataset_feeds = extract_dataset_feed_urls(feed_json)
    
    print(f"\nFound {len(dataset_feeds)} dataset feeds")
    print(f"\nFirst 10 dataset feed URLs:")
    
    for i, entry in enumerate(dataset_feeds[:10], 1):
        print(f"\n{i}. Title: {entry['title'][:80]}")
        print(f"   URL: {entry['dataset_feed_url']}")
    
    # Output all URLs to a file for further processing
    output_file = Path(__file__).parent.parent / "dataset_feeds.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in dataset_feeds:
            f.write(f"{entry['dataset_feed_url']}\n")
    
    print(f"\n✓ Saved {len(dataset_feeds)} dataset feed URLs to: {output_file}")

if __name__ == '__main__':
    main()
