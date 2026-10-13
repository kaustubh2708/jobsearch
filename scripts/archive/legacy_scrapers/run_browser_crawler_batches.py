#!/usr/bin/env python3
"""
Batch Runner for Autonomous Browser Fresher Crawler Agent
Executes batches of companies from config/companies.txt, scrolling through
company career pages with headless Chrome and discovering verified fresher-eligible roles.
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime, timezone

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_DIR, 'data')
CONFIG_DIR = os.path.join(WORKSPACE_DIR, 'config')

def run_batches(num_batches=4, batch_size=6, start_batch=0):
    comp_file = os.path.join(CONFIG_DIR, 'companies.txt')
    with open(comp_file) as f:
        all_comps = [line.strip() for line in f if line.strip()]

    print("============================================================")
    print("RUNNING AUTONOMOUS BROWSER FRESHER CRAWLER IN BATCHES")
    print(f"Total Companies in Pool: {len(all_comps)}")
    print(f"Batches to Run: {num_batches} (Batch size: {batch_size}, Starting at batch: {start_batch})")
    print("============================================================")

    crawler_script = os.path.join(WORKSPACE_DIR, 'scripts', 'browser_fresher_crawler.py')

    for b in range(start_batch, start_batch + num_batches):
        start_idx = b * batch_size
        end_idx = min(start_idx + batch_size, len(all_comps))
        if start_idx >= len(all_comps):
            print(f"Batch {b}: All companies exhausted.")
            break

        batch_comps = all_comps[start_idx:end_idx]
        print(f"\n>>> Running Batch {b} ({len(batch_comps)} companies): {', '.join(batch_comps)}")

        cmd = [
            sys.executable,
            crawler_script,
            "--batch-index", str(b),
            "--batch-size", str(batch_size)
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            print(res.stdout)
            if res.stderr:
                print("Errors/Warnings:", res.stderr[:300])
        except subprocess.TimeoutExpired:
            print(f"Batch {b} timed out after 180 seconds.")
        except Exception as e:
            print(f"Batch {b} encountered exception: {e}")

    # Check findings
    out_file = os.path.join(DATA_DIR, 'browser_discovered_freshers.json')
    if os.path.exists(out_file):
        with open(out_file) as f:
            records = json.load(f)
        print("\n============================================================")
        print(f"TOTAL VERIFIED FRESHER DISCOVERIES ACROSS BATCHES: {len(records)}")
        print("============================================================")
        for idx, r in enumerate(records, 1):
            print(f"{idx}. [{r.get('company')}] {r.get('title')} ({r.get('location')}) - {r.get('canonical_url')[:65]}")
            print(f"   Experience Note: {r.get('experience_text_actual')[:90]}")
    else:
        print("\nNo output file generated.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-batches", type=int, default=3, help="Number of batches to run")
    parser.add_argument("--batch-size", type=int, default=5, help="Companies per batch")
    parser.add_argument("--start-batch", type=int, default=0, help="Starting batch index")
    args = parser.parse_args()

    run_batches(num_batches=args.num_batches, batch_size=args.batch_size, start_batch=args.start_batch)
