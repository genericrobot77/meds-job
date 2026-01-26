#!/usr/bin/env python3
"""
Process NCTS distribution zip files and Medicine Shortages CSVs.
Run from the project root directory.
"""

import os
import zipfile
import shutil
import re
import glob

# Configuration - relative to script location (project root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(SCRIPT_DIR, "WorkingFiles")
UPLOAD_DIR = os.path.join(SCRIPT_DIR, "Files for upload")
AMT_TERM_DIR = os.path.join(UPLOAD_DIR, "AMTv4", "Terminology")
AMT_MAP_DIR = os.path.join(UPLOAD_DIR, "AMTv4", "Map")


def setup_dirs():
    """Ensure destination directories exist."""
    os.makedirs(AMT_TERM_DIR, exist_ok=True)
    os.makedirs(AMT_MAP_DIR, exist_ok=True)
    print(f"Directories verified in {UPLOAD_DIR}")


def find_latest_zip(directory):
    """Find the latest NCTS distribution zip file."""
    zips = glob.glob(os.path.join(directory, "NCTS_SCT_RF2_DISTRIBUTION_*.zip"))
    if not zips:
        return None
    return max(zips, key=os.path.getmtime)


def remove_suffix(filename):
    """Removes _AUxxxx_xxxxxxxx suffix from filename."""
    pattern = r"_AU\d+_\d+"
    return re.sub(pattern, "", filename)


def process_ncts_zip(zip_path):
    """Extract and rename required files from NCTS zip."""
    print(f"Processing zip: {zip_path}")
    extract_root = os.path.join(WORKING_DIR, "extracted_temp")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_root)

    # Locate Relationship_Snapshot
    rel_files = glob.glob(os.path.join(
        extract_root, "**", "Snapshot", "Terminology", "*Relationship_Snapshot*.txt"
    ), recursive=True)

    if rel_files:
        src = rel_files[0]
        filename = os.path.basename(src)
        new_filename = remove_suffix(filename)
        dest = os.path.join(AMT_TERM_DIR, new_filename)
        shutil.copy2(src, dest)
        print(f"Copied & Renamed: {filename} -> {dest}")
    else:
        print("Warning: Relationship_Snapshot file not found in zip.")

    # Locate SimpleMapSnapshot
    map_files = glob.glob(os.path.join(
        extract_root, "**", "Snapshot", "Refset", "Map", "*SimpleMapSnapshot*.txt"
    ), recursive=True)

    if map_files:
        src = map_files[0]
        filename = os.path.basename(src)
        new_filename = remove_suffix(filename)
        dest = os.path.join(AMT_MAP_DIR, new_filename)
        shutil.copy2(src, dest)
        print(f"Copied & Renamed: {filename} -> {dest}")
    else:
        print("Warning: SimpleMapSnapshot file not found in zip.")

    # Cleanup extraction
    shutil.rmtree(extract_root)


def process_shortages():
    """Rename Medicine Shortages file to standard name."""
    candidates = (
        glob.glob(os.path.join(WORKING_DIR, "*Shortages*.csv")) +
        glob.glob(os.path.join(WORKING_DIR, "*Shortages*.xls*"))
    )
    target_name = "MedicineShortagesActiveResultSummaryExport.csv"
    target_path = os.path.join(WORKING_DIR, target_name)

    # Filter out target if already exists
    candidates = [c for c in candidates if os.path.basename(c) != target_name]

    if candidates:
        src = candidates[0]
        shutil.move(src, target_path)
        print(f"Renamed shortages file: {src} -> {target_path}")
    elif os.path.exists(target_path):
        print(f"Shortages file already exists as {target_name}")
    else:
        print("No Medicine Shortages file found to process.")


def main():
    print("Starting NCTS Data Processing...")

    if not os.path.exists(WORKING_DIR):
        print(f"Error: Working directory not found at {WORKING_DIR}")
        print("Create WorkingFiles/ and add input files.")
        return

    setup_dirs()

    zip_file = find_latest_zip(WORKING_DIR)
    if zip_file:
        process_ncts_zip(zip_file)
    else:
        print("No NCTS distribution zip found in WorkingFiles.")

    process_shortages()
    print("Processing complete.")


if __name__ == "__main__":
    main()
