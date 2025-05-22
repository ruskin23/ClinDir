#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper functions for various tasks including file system operations,
PDF processing, data batching, and progress tracking.
"""

# --- Imports ---
import os
import hashlib
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Iterator, Generator, Union

from pdfminer.high_level import extract_text

from models import FileDescriptor


# --- File System Utilities ---

def file_hash(filepath: str) -> str:
    """
    Computes the SHA256 hash of a file.

    Args:
        filepath: Path to the file.

    Returns:
        The hex digest of the file's SHA256 hash.
    """
    hasher = hashlib.sha256()
    path_obj = Path(filepath)
    with path_obj.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def list_pdfs(root_dir: str) -> List[str]:
    """
    Lists the basenames of all PDF files (*.pdf) in the specified root directory.

    Args:
        root_dir: The path to the directory to scan.

    Returns:
        A list of PDF file basenames found in the root directory.
    """
    pdf_filenames = []
    root_path = Path(root_dir)
    if not root_path.is_dir():
        # Or raise an error: raise FileNotFoundError(f"Directory not found: {root_dir}")
        return []
    for entry in root_path.iterdir():
        if entry.is_file() and entry.suffix.lower() == '.pdf':
            pdf_filenames.append(entry.name)
    return sorted(pdf_filenames)


def get_directory_structure(root: str, format: str = "dict") -> Union[Dict[str, Any], List[str], str]:
    """
    Return the directory structure of `root`, relative to it.

    Formats:
    - 'dict' : Nested dictionaries representing the directory structure.
               Files are represented as keys with `None` as their value.
    - 'tree' : A string representation similar to the output of the `tree` command.
    - 'list' : A sorted list of relative file paths (e.g., './file.txt', './subdir/file.txt').

    Args:
        root: The root directory path.
        format: The desired output format ("dict", "tree", or "list").

    Returns:
        The directory structure in the specified format.

    Raises:
        ValueError: If an unsupported format is requested.
        FileNotFoundError: If the root directory does not exist.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"Root directory '{root}' not found.")

    # Build the dictionary structure first (needed for 'dict' and 'tree')
    dir_dict_structure: Dict[str, Any] = {}
    for dirpath_str, _, filenames in os.walk(root):
        dirpath_p = Path(dirpath_str)
        relative_dir_p = dirpath_p.relative_to(root_path)

        current_level = dir_dict_structure
        if str(relative_dir_p) != ".":  # Not the root directory itself
            for part in relative_dir_p.parts:
                current_level = current_level.setdefault(part, {})

        for file_name in filenames:
            current_level[file_name] = None  # Mark files with None

    if format == "dict":
        return dir_dict_structure

    elif format == "list":
        paths: List[str] = []
        for dirpath_str, _, filenames in os.walk(root):
            current_dir_path = Path(dirpath_str)
            for f_name in filenames:
                file_path = current_dir_path / f_name
                relative_file_path = file_path.relative_to(root_path)
                paths.append(f"./{relative_file_path}")
        return sorted(paths)

    elif format == "tree":
        def build_tree_str(d: Dict[str, Any], prefix: str = "") -> List[str]:
            tree_lines: List[str] = []
            items = list(d.items())
            for i, (name, content) in enumerate(items):
                connector = "└── " if i == len(items) - 1 else "├── "
                tree_lines.append(prefix + connector + name)
                if isinstance(content, dict):  # It's a directory
                    next_prefix = prefix + ("    " if i == len(items) - 1 else "│   ")
                    tree_lines.extend(build_tree_str(content, next_prefix))
            return tree_lines

        # The root itself is represented by "."
        return ".\n" + "\n".join(build_tree_str(dir_dict_structure))

    else:
        raise ValueError(f"Unsupported format: {format}. Choose from 'dict', 'list', or 'tree'.")


def copy_files_if_new_path_exists(batch_descriptors: List[FileDescriptor], output_dir: str) -> None:
    """
    Copies files based on FileDescriptor objects if a new file path is specified.

    For each FileDescriptor in the batch:
    - If `newFilePath` is provided, the file from `oldFilePath` is copied.
    - `newFilePath` is adjusted:
        - If it starts with './', './' is replaced by `output_dir`.
        - If it's relative (and not starting with './'), `output_dir` is prepended.
        - If it's absolute, it's used as is (a warning is printed).
    - Directories for `newFilePath` are created if they don't exist.

    Args:
        batch_descriptors: A list of FileDescriptor objects.
        output_dir: The base directory to prepend or use for relative new file paths.
    """
    output_dir_path = Path(output_dir)

    for descriptor in batch_descriptors:
        print(f"Processing ID: {descriptor.id}")
        if descriptor.newFilePath:
            old_path = Path(descriptor.oldFilePath)
            original_new_path_str = descriptor.newFilePath

            # Determine the final new path
            new_fp_candidate = Path(original_new_path_str)
            target_copy_path: Path

            if new_fp_candidate.is_absolute():
                target_copy_path = new_fp_candidate
                print(f"  Warning: newFilePath '{original_new_path_str}' for ID: {descriptor.id} is an absolute path. Not prepending output_dir.")
            else:
                # Handle paths relative to 'output_dir'
                path_segment = original_new_path_str
                if original_new_path_str.startswith("./"):
                    path_segment = original_new_path_str[2:] # Strip './'
                elif original_new_path_str.startswith(".\\"): # Windows case
                    path_segment = original_new_path_str[2:] # Strip '.\\'
                target_copy_path = output_dir_path / path_segment

            print(f"  Original newFilePath: '{original_new_path_str}'")
            print(f"  OldFilePath: '{old_path}'")
            print(f"  Processed newFilePath for copy: '{target_copy_path}'")

            # Create the target directory if it doesn't exist
            target_dir = target_copy_path.parent
            if not target_dir.exists():
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    print(f"  Created directory: {target_dir}")
                except OSError as e:
                    print(f"  Error creating directory {target_dir}: {e}. Skipping copy for this file.")
                    continue  # Skip to the next descriptor

            # Perform the copy operation
            try:
                if not old_path.exists():
                    print(f"  Error: Source file not found at '{old_path}'")
                    continue

                shutil.copy2(str(old_path), str(target_copy_path)) # shutil often prefers str paths
                print(f"  Successfully copied '{old_path}' to '{target_copy_path}'")
            except FileNotFoundError: # Should be caught by old_path.exists(), but good to have
                print(f"  Error: Source file not found at '{old_path}' (should have been caught earlier).")
            except PermissionError:
                print(f"  Error: Permission denied when copying from '{old_path}' to '{target_copy_path}'.")
            except Exception as e:
                print(f"  An unexpected error occurred while copying '{old_path}' to '{target_copy_path}': {e}")
        else:
            print(f"  Skipping file with ID: {descriptor.id} because newFilePath is empty or None.")
        print("-" * 30)  # Separator for clarity

# --- PDF Processing ---

def extract_text_from_pdf(pdf_path: str, max_pages: int = 20) -> str:
    """
    Extracts text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum number of pages to extract text from.

    Returns:
        The extracted text as a single string.
    """
    try:
        return extract_text(pdf_path, maxpages=max_pages)
    except Exception as e:
        print(f"Error extracting text from '{pdf_path}': {e}")
        return ""

# --- Data Handling & Tracking ---

def batchify(iterable: List[Any], batch_size: int) -> Generator[List[Any], None, None]:
    """
    Yields successive n-sized chunks from an iterable.

    Args:
        iterable: The list or sequence to batch.
        batch_size: The size of each batch.

    Yields:
        A list representing a batch of items from the iterable.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]


def get_processed_files(tracking_file_path: str) -> List[str]:
    """
    Retrieves a list of 'id's from a JSON tracking file.

    If the tracking file doesn't exist, it's created with an empty list.

    Args:
        tracking_file_path: Path to the JSON tracking file.

    Returns:
        A list of file 'id's that have been processed.
    """
    tracking_file = Path(tracking_file_path)

    if not tracking_file.exists():
        try:
            tracking_file.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            tracking_file.write_text("[]", encoding='utf-8')
            return []
        except OSError as e:
            print(f"Error creating tracking file '{tracking_file}': {e}")
            return [] # Or raise

    try:
        with tracking_file.open('r', encoding='utf-8') as f:
            tracked_items = json.load(f)
        if not isinstance(tracked_items, list):
            print(f"Warning: Tracking file '{tracking_file}' does not contain a JSON list. Reinitializing.")
            tracking_file.write_text("[]", encoding='utf-8')
            return []
        # Ensure items are dictionaries with 'id' key
        hash_ids = [item['id'] for item in tracked_items if isinstance(item, dict) and 'id' in item]
        return hash_ids
    except json.JSONDecodeError:
        print(f"Error: Tracking file '{tracking_file}' contains invalid JSON. Returning empty list.")
        # Optionally, backup the corrupted file and create a new one
        return []
    except Exception as e: # Catch other potential errors like permission issues
        print(f"Error reading tracking file '{tracking_file}': {e}")
        return []


def save_batch(batch_data: List[FileDescriptor], tracking_file_path: str) -> None:
    """
    Appends a batch of FileDescriptor data to a JSON tracking file.

    If the tracking file doesn't exist, it's created.
    FileDescriptor objects are converted to dictionaries using `model_dump()`.

    Args:
        batch_data: A list of FileDescriptor objects to save.
        tracking_file_path: Path to the JSON tracking file.
    """
    tracking_file = Path(tracking_file_path)

    try:
        if not tracking_file.exists():
            tracking_file.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            tracked_files_data: List[Dict[str, Any]] = []
        else:
            with tracking_file.open('r', encoding='utf-8') as f:
                try:
                    content = f.read()
                    if not content.strip(): # File is empty or whitespace
                        tracked_files_data = []
                    else:
                        tracked_files_data = json.loads(content)
                    if not isinstance(tracked_files_data, list):
                        print(f"Warning: Tracking file '{tracking_file}' was not a list. Reinitializing.")
                        tracked_files_data = []
                except json.JSONDecodeError:
                    print(f"Warning: Tracking file '{tracking_file}' contained invalid JSON. Reinitializing.")
                    # Optionally, backup corrupted file here
                    tracked_files_data = []

        # Convert FileDescriptor objects to their dictionary representation
        batch_to_save = [fd.model_dump() for fd in batch_data]
        tracked_files_data.extend(batch_to_save)

        with tracking_file.open('w', encoding='utf-8') as f:
            json.dump(tracked_files_data, f, indent=2)

    except IOError as e:
        print(f"IOError saving batch to tracking file '{tracking_file}': {e}")
    except Exception as e: # Catch other potential errors
        print(f"An unexpected error occurred while saving batch to '{tracking_file}': {e}")

