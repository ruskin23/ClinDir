#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main script for processing PDF documents:
- Computes file hashes
- Extracts text from PDFs
- Applies renaming logic via NameChanger
- Saves metadata and copies renamed files
- Tracks processed files to avoid duplication
"""

import os
import argparse
from pathlib import Path
from typing import Optional, List

from helpers import (
    file_hash,
    extract_text_from_pdf,
    list_pdfs,
    get_processed_files,
    save_batch,
    copy_files_if_new_path_exists,
    batchify
)
from generators import NameChanger
from models import FileDescriptor


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for PDF processing.

    Returns:
        Parsed arguments as a Namespace object.
    """
    parser = argparse.ArgumentParser(
        description="Process PDFs and track processed files."
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
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,
        help='Size of each processing batch'
    )
    
    args = parser.parse_args()

    if not args.pdf_dir.is_dir():
        parser.error(f"The PDF directory does not exist: {args.pdf_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    return args


def rename_file(filepath: str, renamer: NameChanger) -> FileDescriptor:
    """
    Generates a new file name and descriptor based on extracted PDF content.

    Args:
        filepath: Path to the PDF file.
        renamer: Instance of NameChanger to generate new name metadata.

    Returns:
        A FileDescriptor instance with updated naming and metadata.
    """
    print(f"\n[INFO] Starting rename process for: {filepath}")

    file_id = file_hash(filepath)
    descriptor = FileDescriptor(
        id=file_id,
        oldFilePath=filepath,
        newFilePath='',
        docDescription='',
        docType=''
    )
    
    text = extract_text_from_pdf(filepath)
    print(f"[DEBUG] Extracted {len(text)} characters from file")

    if not text:
        print(f"[WARN] No text extracted from: {filepath}")
        return descriptor

    name_info = renamer.process_document(text=text)
    print(f"[DEBUG] Renaming info: {name_info.model_dump()}")

    new_filepath = os.path.join(name_info.pathToFile, name_info.newFileName)

    descriptor.newFilePath = new_filepath
    descriptor.docDescription = name_info.description
    descriptor.docType = name_info.docType

    print(f"[INFO] New file path determined: {new_filepath}")

    return descriptor


def main():
    """
    Main execution logic for the PDF processing pipeline.
    """
    args = parse_args()

    print(f"[SETUP] Input directory:  {args.pdf_dir}")
    print(f"[SETUP] Output directory: {args.output_dir}")
    print(f"[SETUP] Tracking file:    {args.tracking_file}")
    print(f"[SETUP] Batch size:       {args.batch_size}")

    saved_ids = get_processed_files(args.tracking_file)
    print(f"[INFO] Loaded {len(saved_ids)} previously processed IDs")

    pdf_files = list_pdfs(args.pdf_dir)
    print(f"[INFO] Found {len(pdf_files)} PDFs to consider for processing")

    renamer = NameChanger()

    for batch_index, batch in enumerate(batchify(pdf_files, args.batch_size), start=1):
        print(f"\n[BATCH {batch_index}] Processing {len(batch)} files")

        batch_descriptors: List[FileDescriptor] = []

        for filename in batch:
            filepath = os.path.join(args.pdf_dir, filename)
            file_id = file_hash(filepath)

            if file_id in saved_ids:
                print(f"[SKIP] File already processed: {filename}")
                continue

            try:
                descriptor = rename_file(filepath, renamer)
                batch_descriptors.append(descriptor)
            except Exception as e:
                print(f"[ERROR] Failed to process '{filename}': {e}")

        if batch_descriptors:
            save_batch(batch_descriptors, args.tracking_file)
            copy_files_if_new_path_exists(batch_descriptors, args.output_dir)
            print(f"[SUCCESS] Batch saved and copied: {len(batch_descriptors)} files")


if __name__ == '__main__':
    main()
