#!/usr/bin/env python3
"""
Research International Codes for New Medicinal Products

This script reads the filtered medicinal products CSV and helps automate
research for DrugBank IDs, ATC codes, Pregnancy Category, and Beers Criteria.

Run from project root. Reads from WorkingFiles/ directory.

Usage:
    python3 research_medicinal_products.py                    # Show summary and generate template
    python3 research_medicinal_products.py --interactive      # Manual data entry mode
    python3 research_medicinal_products.py --claude           # Output prompts for Claude Code research
    python3 research_medicinal_products.py --antigravity      # Output prompts for Antigravity Agent
    python3 research_medicinal_products.py --generate         # Generate reference doc from research_data.json

Research Modes:
    --claude       Use when you have Claude Code available (web search via Claude)
    --antigravity  Use when you have Antigravity Agent quota (preferred for deeper research)
    --interactive  Manual entry mode when neither AI agent is available
"""

import csv
import os
import glob
import sys
import json
from datetime import datetime
import urllib.parse
import subprocess
import re

# Configuration - relative to script location (project root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(SCRIPT_DIR, "WorkingFiles")
REFERENCE_DIR = os.path.join(SCRIPT_DIR, "ReferenceFiles")

# Research data file (stores completed research)
RESEARCH_DATA_FILE = os.path.join(WORKING_DIR, "research_data.json")

# Reference files
BEERS_CRITERIA_FILE = os.path.join(REFERENCE_DIR, "Beers_Criteria_2025.csv")

# Reference document output
REFERENCE_DOC_PATTERN = "MedicinalProducts-Research-{date_range}.csv"


def load_beers_criteria():
    """Load Beers Criteria reference data from CSV."""
    beers_data = {}
    if not os.path.exists(BEERS_CRITERIA_FILE):
        print(f"Warning: Beers Criteria file not found at {BEERS_CRITERIA_FILE}")
        return beers_data

    try:
        with open(BEERS_CRITERIA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prefLabel = row.get('prefLabel', '').strip().lower()
                beers_value = row.get('Beers', '').strip().upper()
                if prefLabel:
                    # Store as True/False boolean, not string
                    beers_data[prefLabel] = beers_value == 'TRUE'
    except Exception as e:
        print(f"Error loading Beers Criteria: {e}")

    return beers_data


def check_beers_criteria(drug_name, beers_data):
    """Check if drug is in Beers Criteria list."""
    if not beers_data:
        return "Not listed"

    drug_lower = drug_name.strip().lower()
    if drug_lower in beers_data:
        return "Listed" if beers_data[drug_lower] else "Not listed"

    return "Not listed"


def find_medicinal_products_csv():
    """Find the filtered medicinal products CSV in WorkingFiles."""
    pattern = os.path.join(WORKING_DIR, "SNOMEDCT-AU-MedicinalProducts-*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def load_medicinal_products(csv_path):
    """Load medicinal products from filtered CSV."""
    products = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
    return products


def load_research_data():
    """Load existing research data if available."""
    if os.path.exists(RESEARCH_DATA_FILE):
        with open(RESEARCH_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_research_data(data):
    """Save research data to JSON file."""
    with open(RESEARCH_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Research data saved to: {RESEARCH_DATA_FILE}")


def create_research_template(products, beers_data=None):
    """Create a research template for new products."""
    research_data = load_research_data()

    for product in products:
        concept_id = product['concept_ID']
        preferred_term = product['preferred_term']
        status = product['status']

        # Only research new products
        if status.lower() != 'new':
            continue

        if concept_id not in research_data:
            # Check Beers Criteria if data available
            beers_value = 'Not listed'
            if beers_data:
                beers_value = check_beers_criteria(preferred_term, beers_data)

            research_data[concept_id] = {
                'preferred_term': preferred_term,
                'concept_ID': concept_id,
                'SNOMED_uri': product.get('SNOMED_uri', ''),
                'status': status,
                'research': {
                    'drugbank_id': '',
                    'drugbank_url': '',
                    'atc_codes': [],
                    'atc_classification': '',
                    'pregnancy_category_au': '',
                    'pregnancy_category_fda': '',
                    'beers_criteria': beers_value,
                    'clinical_notes': '',
                    'is_single_substance': None,
                    'researched_date': ''
                }
            }

    return research_data


def generate_reference_document(products, research_data, output_path):
    """Generate the reference CSV document with research findings."""

    headers = [
        'preferred_term',
        'concept_ID',
        'SNOMED_uri',
        'status',
        'drugbank_id',
        'atc_codes',
        'atc_classification',
        'pregnancy_category_au',
        'pregnancy_category_fda',
        'beers_criteria',
        'is_single_substance',
        'clinical_notes',
        'researched_date'
    ]

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for product in products:
            concept_id = product['concept_ID']

            # Get research data if available
            research = research_data.get(concept_id, {}).get('research', {})

            row = {
                'preferred_term': product['preferred_term'],
                'concept_ID': concept_id,
                'SNOMED_uri': product.get('SNOMED_uri', ''),
                'status': product['status'],
                'drugbank_id': research.get('drugbank_id', ''),
                'atc_codes': '; '.join(research.get('atc_codes', [])) if isinstance(research.get('atc_codes'), list) else research.get('atc_codes', ''),
                'atc_classification': research.get('atc_classification', ''),
                'pregnancy_category_au': research.get('pregnancy_category_au', ''),
                'pregnancy_category_fda': research.get('pregnancy_category_fda', ''),
                'beers_criteria': research.get('beers_criteria', ''),
                'is_single_substance': research.get('is_single_substance', ''),
                'clinical_notes': research.get('clinical_notes', ''),
                'researched_date': research.get('researched_date', '')
            }
            writer.writerow(row)

    print(f"Reference document generated: {output_path}")


def display_research_summary(products, research_data):
    """Display summary of products needing research."""
    new_products = [p for p in products if p['status'].lower() == 'new']

    print("\n" + "=" * 70)
    print("MEDICINAL PRODUCTS RESEARCH SUMMARY")
    print("=" * 70)
    print(f"Total products: {len(products)}")
    print(f"New products requiring research: {len(new_products)}")
    print("=" * 70)

    if new_products:
        print("\nProducts to research:")
        print("-" * 70)
        for idx, product in enumerate(new_products, 1):
            concept_id = product['concept_ID']
            has_research = concept_id in research_data and research_data[concept_id].get('research', {}).get('researched_date')
            status_icon = "✓" if has_research else "○"

            print(f"\n{idx}. [{status_icon}] {product['preferred_term']}")
            print(f"   SNOMED Code: {concept_id}")
            print(f"   SNOMED URI: {product.get('SNOMED_uri', 'N/A')}")

            if has_research:
                r = research_data[concept_id]['research']
                if r.get('drugbank_id'):
                    print(f"   DrugBank: {r['drugbank_id']}")
                if r.get('atc_codes'):
                    atc = '; '.join(r['atc_codes']) if isinstance(r['atc_codes'], list) else r['atc_codes']
                    print(f"   ATC: {atc}")
                if r.get('pregnancy_category_au'):
                    print(f"   Pregnancy (AU): {r['pregnancy_category_au']}")


def print_research_urls():
    """Print useful research URLs."""
    print("\n" + "=" * 70)
    print("RESEARCH RESOURCES")
    print("=" * 70)
    print("DrugBank:      https://go.drugbank.com/")
    print("WHO ATC Index: https://www.whocc.no/atc_ddd_index/")
    print("TGA Database:  https://www.tga.gov.au/resources/health-professional-information-and-resources/australian-categorisation-system-prescribing-medicines-pregnancy/prescribing-medicines-pregnancy-database")
    print("Beers Criteria: American Geriatrics Society Beers Criteria (2023)")
    print("=" * 70)


def perform_claude_research_interactive():
    """Perform Claude web searches in real-time during conversation."""
    print("\n" + "=" * 70)
    print("CLAUDE CODE RESEARCH MODE - INTERACTIVE")
    print("=" * 70)
    print()
    print("I can now search the web for the drug codes in real-time.")
    print()
    print("Send me the unresearched products and I will:")
    print("  1. Search DrugBank for IDs")
    print("  2. Search WHO ATC database for ATC codes")
    print("  3. Search for Pregnancy Categories")
    print("  4. Search for Beers Criteria status")
    print()
    print("Then provide JSON results you can paste into research_data.json")
    print()
    print("List the products you want researched:")
    print("=" * 70)

    # Show unresearched products
    csv_path = find_medicinal_products_csv()
    if csv_path:
        products = load_medicinal_products(csv_path)
        research_data = load_research_data()

        new_products = [p for p in products if p['status'].lower() == 'new']
        unresearched = [p for p in new_products
                        if p['concept_ID'] not in research_data
                        or not research_data[p['concept_ID']].get('research', {}).get('researched_date')]

        if unresearched:
            print("\nUnresearched products:")
            for product in unresearched:
                print(f"  - {product['preferred_term']}")
            print()
            print("Paste this list to Claude Code (me) and I'll search for all codes.")
        else:
            print("\nAll products have been researched!")
    print("=" * 70)


def generate_claude_prompts(products, research_data):
    """Generate prompts for Claude Code to research each product."""
    new_products = [p for p in products if p['status'].lower() == 'new']
    unresearched = [p for p in new_products
                    if p['concept_ID'] not in research_data
                    or not research_data[p['concept_ID']].get('research', {}).get('researched_date')]

    if not unresearched:
        print("\nAll products have been researched!")
        return

    print("\n" + "=" * 70)
    print("CLAUDE CODE RESEARCH MODE (DIRECT WEBSITE LOOKUP)")
    print("=" * 70)
    print()
    print("COST SAVING TIP: Already on Haiku model - ready to go!")
    print()
    print("Instructions:")
    print("  1. Copy the prompt below")
    print("  2. Paste into Claude Code")
    print("  3. Research using ONLY the specified websites (no web search needed)")
    print("  4. Update WorkingFiles/research_data.json with results")
    print()
    print("Copy the prompt below and paste it to Claude Code:")
    print("-" * 70)

    product_list = "\n".join([f"  - {p['preferred_term']} (SNOMED: {p['concept_ID']})"
                              for p in unresearched])

    prompt = f"""# Medicinal Product Research Task

Research the following new Australian medicinal products by fetching data from official websites.

## Products to Research
{product_list}

## Research Instructions - Use WebFetch to get data from these sites

### For each product:

1. **DrugBank Search** - Use WebFetch to search:
   - Try: https://go.drugbank.com/drugs?q=DRUGNAME
   - Extract DB##### ID from the results (e.g., DB17449)
   - Only for single-substance drugs (skip combinations)

2. **ATC Code Search** - Use WebFetch to search:
   - Try: https://atcddd.fhi.no/atc_ddd_index/?code=&showdescription=yes&search=DRUGNAME
   - Extract the ATC code (e.g., D03BA03, B06AC08)
   - Note the classification (e.g., "Proteolytic enzymes")

3. **Pregnancy Category** (Optional)
   - Only if easily found in DrugBank or other sources
   - Leave blank if not readily available

4. **Beers Criteria**
   - Default to "Not listed" (most new drugs aren't listed)

5. **Clinical Notes**
   - Brief description from DrugBank or product info

## Instructions
Use the WebFetch tool to query the websites above for each drug. Extract the information and compile results.

## Output Format
Provide results in JSON:
```json
{{
  "933623411000036106": {{
    "preferred_term": "Anacaulase-bcdb",
    "drugbank_id": "DB17449",
    "atc_codes": ["D03BA03"],
    "atc_classification": "Proteolytic enzymes",
    "pregnancy_category_au": "",
    "pregnancy_category_fda": "",
    "beers_criteria": "Not listed",
    "is_single_substance": true,
    "clinical_notes": "Description here",
    "researched_date": "{datetime.now().strftime('%Y-%m-%d')}"
  }}
}}
```

## Next Steps
After you complete research and provide the JSON:
1. Open WorkingFiles/research_data.json
2. Update each product's "research" object with your findings
3. Save the file
4. Run: python3 research_medicinal_products.py --generate
"""
    print(prompt)
    print("-" * 70)


def search_atc_code(drug_name):
    """Generate a prompt for Claude to search web for a specific drug's ATC code."""
    print("\n" + "=" * 70)
    print(f"WEB SEARCH FOR ATC CODE: {drug_name}")
    print("=" * 70)
    print()
    print("Copy this prompt and paste it to Claude Code:")
    print("-" * 70)

    prompt = f"""Search the web for the ATC code for "{drug_name}".

Use web search to find:
1. **ATC Code** (e.g., D03BA03, B06AC08, J07BN01)
2. **ATC Classification** (the full classification name)

Search the WHO ATC database or medical databases for this drug.

Return the results in this format:
```
ATC Code: [CODE]
Classification: [FULL CLASSIFICATION DESCRIPTION]
Source: [where you found it]
```

If multiple ATC codes exist for this drug, list them all.
If no code found, indicate that it may be pending or not yet assigned.
"""
    print(prompt)
    print("-" * 70)
    print("\nAfter getting results from Claude, add to research_data.json:")
    print(f'  "atc_codes": ["CODE1", "CODE2"],')
    print(f'  "atc_classification": "Classification description"')
    print("=" * 70)


def generate_antigravity_prompts(products, research_data):
    """Generate prompts for Antigravity Agent to research each product."""
    new_products = [p for p in products if p['status'].lower() == 'new']
    unresearched = [p for p in new_products
                    if p['concept_ID'] not in research_data
                    or not research_data[p['concept_ID']].get('research', {}).get('researched_date')]

    if not unresearched:
        print("\nAll products have been researched!")
        return

    print("\n" + "=" * 70)
    print("ANTIGRAVITY AGENT RESEARCH MODE (DIRECT WEBSITE LOOKUP)")
    print("=" * 70)
    print("Copy this prompt for Antigravity Agent:")
    print("-" * 70)

    product_list = "\n".join([f"  - {p['preferred_term']} (SNOMED ID: {p['concept_ID']}, URI: {p.get('SNOMED_uri', 'N/A')})"
                              for p in unresearched])

    prompt = f"""# Medicinal Product Research Task

Research the following new Australian medicinal products using DIRECT website lookups.

## Products to Research
{product_list}

## Research Method - USE THESE WEBSITES DIRECTLY (No web search needed)

### 1. DrugBank ID - https://go.drugbank.com/
- Search the drug name directly on the site
- Extract the DB##### ID from the URL (e.g., DB17449)
- **Only for single-substance medications** - skip combinations, acetate/phosphate variations
- If no result, leave blank

### 2. ATC Code - https://atcddd.fhi.no/atc_ddd_index/
- Search the drug name or active ingredient
- Record the ATC code (e.g., D03BA03, B06AC08)
- Include full classification (e.g., "D03BA - Proteolytic enzymes")
- Very new drugs may not have codes yet - note as "Pending" if not found

### 3. Pregnancy Category (Australian TGA preferred)
- TGA Database: https://www.tga.gov.au/prescribing-medicines-pregnancy-database
- Australian categories: A, B1, B2, B3, C, D, X
- If not in TGA, note "Not found in TGA"
- FDA information is secondary (no letter categories since 2015)

### 4. Beers Criteria
- American Geriatrics Society Beers Criteria
- Most new drugs won't be listed
- Default: "Not listed"

### 5. Clinical Notes
- Drug class, indication, brand name
- Can source from DrugBank product pages

## Output Format
Provide JSON results:
```json
{{
  "concept_ID": {{
    "preferred_term": "Drug Name",
    "drugbank_id": "DB#####",
    "atc_codes": ["D03BA03"],
    "atc_classification": "Classification name",
    "pregnancy_category_au": "Category or blank",
    "pregnancy_category_fda": "Optional",
    "beers_criteria": "Not listed",
    "is_single_substance": true/false,
    "clinical_notes": "Brief description",
    "researched_date": "{datetime.now().strftime('%Y-%m-%d')}"
  }}
}}
```

## Notes
- Use only the specified websites - no general web searches needed
- If information not found on site, leave field blank
- For combination drugs, research each component separately if applicable
- Prioritize Australian sources (TGA)
"""
    print(prompt)
    print("-" * 70)
    print("\nAfter Antigravity completes research:")
    print(f"1. Copy the JSON results")
    print(f"2. Update: WorkingFiles/research_data.json")
    print(f"3. Run: python3 research_medicinal_products.py --generate")


def update_research_interactively(research_data):
    """Interactive mode to update research data with detailed guidance."""
    new_products = [data for data in research_data.values()
                    if data['status'].lower() == 'new'
                    and not data.get('research', {}).get('researched_date')]

    if not new_products:
        print("\nAll products have been researched!")
        return research_data

    print("\n" + "=" * 70)
    print("INTERACTIVE RESEARCH MODE")
    print("=" * 70)
    print(f"Found {len(new_products)} products to research")
    print()
    print("For each product:")
    print("  • Press Enter to skip a field")
    print("  • Type 's' to skip this product and come back later")
    print("  • Type 'q' to quit and save progress")
    print("=" * 70)

    completed = 0
    for idx, data in enumerate(new_products, 1):
        concept_id = data['concept_ID']
        preferred_term = data['preferred_term']
        research = data.get('research', {})

        print(f"\n[{idx}/{len(new_products)}] {preferred_term}")
        print(f"SNOMED: {concept_id}")
        print("-" * 70)

        # DrugBank ID
        print("\n1. DrugBank ID")
        print("   Search: https://go.drugbank.com/")
        print("   Format: DB##### (e.g., DB17449)")
        print("   Note: Only for single-substance drugs, skip combinations")
        drugbank = input("   Enter DrugBank ID (or press Enter to skip): ").strip()
        if drugbank.lower() == 'q':
            break
        if drugbank.lower() == 's':
            continue
        if drugbank:
            research['drugbank_id'] = drugbank
            research['drugbank_url'] = f"https://go.drugbank.com/drugs/{drugbank}"
            research['is_single_substance'] = True

        # ATC Codes
        print("\n2. ATC Code(s)")
        print("   Search: https://atcddd.fhi.no/atc_ddd_index/")
        print("   Format: D03BA03 or B06AC08 (may have multiple)")
        print("   Note: Very new drugs may not have ATC codes yet")
        print("   If not found on direct site, can use: python3 research_medicinal_products.py --search-atc '{preferred_term}'")
        atc = input("   Enter ATC code(s), comma-separated (or press Enter): ").strip()
        if atc.lower() == 'q':
            break
        if atc.lower() == 's':
            continue
        if atc:
            research['atc_codes'] = [c.strip() for c in atc.split(',')]

        # ATC Classification
        if research.get('atc_codes'):
            print("\n3. ATC Classification (description of what the code means)")
            print("   Example: 'Proteolytic enzymes' or 'Drugs used in hereditary angioedema'")
            atc_class = input("   Enter classification (or press Enter): ").strip()
            if atc_class.lower() == 'q':
                break
            if atc_class.lower() == 's':
                continue
            if atc_class:
                research['atc_classification'] = atc_class

        # Pregnancy Category AU
        print("\n4. Pregnancy Category (Australian TGA)")
        print("   Search: https://www.tga.gov.au/prescribing-medicines-pregnancy-database")
        print("   Categories: A, B1, B2, B3, C, D, X")
        print("   Note: This field is optional")
        preg_au = input("   Enter category (or press Enter to skip): ").strip()
        if preg_au.lower() == 'q':
            break
        if preg_au.lower() == 's':
            continue
        if preg_au:
            research['pregnancy_category_au'] = preg_au

        # Pregnancy Category FDA
        print("\n5. Pregnancy Category (FDA - optional)")
        print("   Note: FDA doesn't use letter categories since 2015")
        preg_fda = input("   Enter category (or press Enter to skip): ").strip()
        if preg_fda.lower() == 'q':
            break
        if preg_fda.lower() == 's':
            continue
        if preg_fda:
            research['pregnancy_category_fda'] = preg_fda

        # Beers Criteria
        print("\n6. Beers Criteria")
        print("   American Geriatrics Society Beers Criteria")
        print("   Options: 'Listed', 'Not listed' (most new drugs aren't)")
        beers = input("   Enter status (default: Not listed) [press Enter]: ").strip()
        if beers.lower() == 'q':
            break
        if beers.lower() == 's':
            continue
        if beers:
            research['beers_criteria'] = beers
        else:
            research['beers_criteria'] = 'Not listed'

        # Single substance (if not already set)
        if research.get('is_single_substance') is None:
            print("\n7. Single Substance Drug?")
            print("   (Single substance = pure drug, Combination = multiple active ingredients)")
            single = input("   Single substance? (Y/N) [press Enter]: ").strip().upper()
            if single == 'Q':
                break
            if single == 'S':
                continue
            if single in ['Y', 'N']:
                research['is_single_substance'] = single == 'Y'

        # Clinical notes
        print("\n8. Clinical Notes (optional)")
        print("   Brief description: drug class, indication, brand name")
        notes = input("   Enter notes (or press Enter to skip): ").strip()
        if notes.lower() == 'q':
            break
        if notes.lower() == 's':
            continue
        if notes:
            research['clinical_notes'] = notes

        # Mark as researched
        research['researched_date'] = datetime.now().strftime('%Y-%m-%d')
        data['research'] = research
        completed += 1

        print(f"\n✓ Research saved for {preferred_term}")

    print("\n" + "=" * 70)
    print(f"COMPLETION SUMMARY")
    print("=" * 70)
    print(f"Researched: {completed}/{len(new_products)} products")
    print("=" * 70)

    return research_data


def print_usage():
    """Print usage information."""
    print("""
Usage: python3 research_medicinal_products.py [OPTIONS]

Options:
    (no args)           Show summary and save research template
    --interactive       Manual data entry with website guidance
    --antigravity       Generate prompts for Antigravity Agent research
    --claude            Use Claude with web search (fallback for missing codes)
    --search-atc DRUG   Search web for specific drug's ATC code
    --generate          Generate reference document from existing research data
    --help              Show this help message

Research Workflow:
    1. Run filter_medicinal_products.py first to identify new products
    2. Run with --interactive and visit direct websites first
    3. For missing ATC codes: run --search-atc DRUGNAME to web search
    4. Update research_data.json with findings
    5. Run with --generate to create final reference document

Examples:
    python3 research_medicinal_products.py --interactive
    python3 research_medicinal_products.py --search-atc "Anacaulase-bcdb"
    python3 research_medicinal_products.py --generate
""")


def main():
    # Handle help
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print_usage()
        sys.exit(0)

    # Handle search-atc mode
    if len(sys.argv) > 1 and sys.argv[1] == '--search-atc':
        if len(sys.argv) < 3:
            print("Error: --search-atc requires a drug name")
            print("Usage: python3 research_medicinal_products.py --search-atc 'Drug Name'")
            sys.exit(1)
        drug_name = ' '.join(sys.argv[2:])
        search_atc_code(drug_name)
        sys.exit(0)

    # Find the filtered CSV
    csv_path = find_medicinal_products_csv()

    if not csv_path:
        print(f"Error: No SNOMEDCT-AU-MedicinalProducts-*.csv found in {WORKING_DIR}")
        print("Run filter_medicinal_products.py first to generate the filtered CSV.")
        sys.exit(1)

    print(f"Reading from: {csv_path}")

    # Load products
    products = load_medicinal_products(csv_path)

    # Load Beers Criteria reference data
    beers_data = load_beers_criteria()
    if beers_data:
        print(f"✓ Loaded Beers Criteria database ({len(beers_data)} drugs)")
    else:
        print("Warning: Beers Criteria database not loaded")

    # Create/load research template
    research_data = create_research_template(products, beers_data)

    # Display summary
    display_research_summary(products, research_data)

    # Check command line args
    mode = sys.argv[1] if len(sys.argv) > 1 else None

    if mode == '--generate':
        # Generate reference document only
        pass

    elif mode == '--claude':
        # Claude Code research mode - interactive
        save_research_data(research_data)
        perform_claude_research_interactive()

    elif mode == '--antigravity':
        # Antigravity Agent mode
        save_research_data(research_data)
        generate_antigravity_prompts(products, research_data)

    elif mode == '--interactive':
        # Interactive mode
        print_research_urls()
        research_data = update_research_interactively(research_data)
        save_research_data(research_data)

    else:
        # Default: save template and print instructions
        save_research_data(research_data)
        print_research_urls()
        print("\n" + "=" * 70)
        print("RESEARCH MODE OPTIONS")
        print("=" * 70)
        print("Choose your research method:")
        print()
        print("  --interactive       Manual entry (with direct website links)")
        print("                      Try direct websites first")
        print()
        print("  --search-atc DRUG   Web search for missing ATC codes")
        print("                      Use when code not found on direct site")
        print("                      Example: --search-atc 'Anacaulase-bcdb'")
        print()
        print("  --antigravity       Antigravity Agent (full automation)")
        print("                      Browser automation for all codes")
        print()
        print("  --claude            Claude web search (fallback)")
        print("                      Alternative when Antigravity unavailable")
        print()
        print("  --generate          Create reference document")
        print()
        print("Examples:")
        print("  python3 research_medicinal_products.py --interactive")
        print("  python3 research_medicinal_products.py --search-atc 'Anacaulase-bcdb'")
        print("  python3 research_medicinal_products.py --generate")
        print("=" * 70)

    # Generate reference document
    input_basename = os.path.basename(csv_path)
    date_range = input_basename.replace("SNOMEDCT-AU-MedicinalProducts-", "").replace(".csv", "")
    output_basename = REFERENCE_DOC_PATTERN.format(date_range=date_range)
    output_path = os.path.join(WORKING_DIR, output_basename)

    generate_reference_document(products, research_data, output_path)

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Review the reference document in WorkingFiles/")
    print("2. Use findings to update AHT in PoolParty")
    print("=" * 70)


if __name__ == "__main__":
    main()
