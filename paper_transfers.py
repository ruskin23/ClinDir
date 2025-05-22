#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
paper_transfers.py

This takes research papers from the stored JSON and converts them into separate .md files.
Useful to organize you Obsidian directory
"""

import json
import os
import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for PDF processing.

    Returns:
        Parsed arguments as a Namespace object.
    """
    parser = argparse.ArgumentParser(
        description="Paper Transfer to Vault."
    )
    
    parser.add_argument(
        '--pdf-dir',
        type=Path,
        required=True,
        help='Path to directory containing input PDF files'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        required=True,
        help='Path to directory where output will be stored'
    )
    
    parser.add_argument(
        '--tracking-file',
        type=Path,
        required=True,
        help='Path to the JSON file used to track processed files'
    )
    
    
    args = parser.parse_args()

    if not args.pdf_dir.is_dir():
        parser.error(f"The PDF directory does not exist: {args.pdf_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    return args

def get_papers_list(tracking_filename):

    with open(tracking_filename, 'r') as f:
        tracked_data = json.load(f)
        
    papers_list = []
    
    for doc in tracked_data:
        if 'paper' in doc['docType']:
            papers_list.append(doc)
    
    return papers_list   

def save_markdowns(args):
    
    papers_list = get_papers_list(args.tracking_filename)
    
    for paper in papers_list:
        filepath = paper["newFilePath"]
        filename = os.path.basename(filepath)
        filename = filename.replace('.pdf', '') 
        
        title = ' '.join(filename.split('_')).strip()
        description = paper['docDescription']
        
        
        md_filename = f"{title}.md"
        md_path = os.path.join(args.output_dir, md_filename)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(description)

        print(f"Saved: {md_path}")
        
        

if __name__ == '__main__':
    
    args = parse_args()
    save_markdowns(args)