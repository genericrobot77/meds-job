#!/usr/bin/env python3
"""
Filter SNOMED CT-AU change report for Medicinal Products only
and generate SNOMED URIs.

Run from project root. Reads from WorkingFiles/, outputs to outputs/ directory.
"""

import csv
import os
import glob
import sys

# Configuration - relative to script location (project root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(SCRIPT_DIR, "WorkingFiles")
OUTPUTS_DIR = os.path.join(SCRIPT_DIR, "outputs")

# Ensure outputs directory exists
os.makedirs(OUTPUTS_DIR, exist_ok=True)

TARGET_SEMANTIC_TAG = "medicinal product"
SNOMED_BASE_URL = "http://snomed.info/id/"


def find_change_report():
    """Find the SNOMED CT-AU change report CSV in WorkingFiles."""
    pattern = os.path.join(WORKING_DIR, "SNOMEDCT-AU-concept-changes-*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def prompt_antigravity_download():
    """Generate Antigravity Agent prompt to download SNOMED CSV from NCTS website."""
    print("\n" + "=" * 70)
    print("SNOMED CSV NOT FOUND - ANTIGRAVITY DOWNLOAD REQUIRED")
    print("=" * 70)
    print("\nThe SNOMEDCT-AU-concept-changes-*.csv file was not found in WorkingFiles/")
    print("\nIf you have Antigravity Agent available, use this prompt:\n")
    print("-" * 70)
    print("""
TASK: Download SNOMED CT-AU Change Report CSV

1. Navigate to: https://www.healthterminologies.gov.au/access-clinical-terminology/access-snomed-ct-au/other/

2. Locate and click the "Download as CSV" button with this selector:
   <button type="button" class="v-btn theme--dark" style="background-color: rgb(19, 94, 112); border-color: rgb(19, 94, 112);"><div class="v-btn__content">Download as CSV</div></button>

3. Save the downloaded file to your local WorkingFiles/ directory with the naming pattern:
   SNOMEDCT-AU-concept-changes-YYYYMMDD-YYYYMMDD.csv

Once downloaded, run this script again:
   python3 filter_medicinal_products.py
""")
    print("-" * 70)
    print("\nAlternatively, manually download the file from the NCTS website and save it to WorkingFiles/")
    print("=" * 70 + "\n")
    sys.exit(1)


def main():
    input_path = find_change_report()

    if not input_path:
        prompt_antigravity_download()

    # Derive output filename from input
    input_basename = os.path.basename(input_path)
    output_basename = input_basename.replace("concept-changes", "MedicinalProducts")
    output_path = os.path.join(OUTPUTS_DIR, output_basename)

    print(f"Reading from: {input_path}")

    medicinal_products = []
    total_rows = 0

    with open(input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        headers = reader.fieldnames

        for row in reader:
            total_rows += 1
            if row['semantic_tag'].strip().lower() == TARGET_SEMANTIC_TAG:
                medicinal_products.append(row)

    # Add SNOMED URI column after concept_ID
    output_headers = list(headers)
    concept_id_index = output_headers.index('concept_ID')
    output_headers.insert(concept_id_index + 1, 'SNOMED_uri')

    print(f"Writing to: {output_path}")

    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_headers)
        writer.writeheader()

        for row in medicinal_products:
            row['SNOMED_uri'] = SNOMED_BASE_URL + row['concept_ID']
            writer.writerow(row)

    # Print summary
    print("\n" + "=" * 60)
    print("FILTERING SUMMARY")
    print("=" * 60)
    print(f"Total rows processed: {total_rows}")
    print(f"Medicinal Products found: {len(medicinal_products)}")
    print(f"Output file: {output_basename}")
    print("=" * 60)

    # Display the medicinal products found
    if medicinal_products:
        print(f"\nMedicinal Products identified ({len(medicinal_products)}):")
        print("-" * 60)
        for idx, mp in enumerate(medicinal_products, 1):
            status = mp['status']
            change_type = mp['change_type']
            inactive_reason = mp['inactive_reason']

            status_info = f"[{status}]"
            if change_type:
                status_info += f" ({change_type})"
            if inactive_reason:
                status_info += f" - {inactive_reason}"

            print(f"{idx}. {mp['preferred_term']} {status_info}")
            print(f"   SNOMED Code: {mp['concept_ID']}")
            print(f"   SNOMED URI: {SNOMED_BASE_URL}{mp['concept_ID']}")

            if mp['target_concept_id']:
                print(f"   → Target: {mp['target_concept_preferred_term']} (ID: {mp['target_concept_id']})")
            print()
    else:
        print("\nNo medicinal products found in the report.")


if __name__ == "__main__":
    main()
