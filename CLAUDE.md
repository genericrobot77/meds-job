# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This project processes NCTS (National Clinical Terminology Service) SNOMED CT RF2 distribution files for Australian Medicines Terminology (AMT) uploads and Australia Health Thesaurus (AHT) updates.

## Monthly Workflow Overview

1. **Download** (Manual): Place files in `WorkingFiles/`
2. **Process** (Automated): Run scripts for Steps 1-2
3. **Research** (Semi-automated): Research international codes for new MPs
4. **Update AHT** (Manual): Import concepts into PoolParty

## Automated Steps

### Step 1: Process NCTS Files and Medicine Shortages

```bash
python3 process_ncts_data.py
```

- Finds latest `NCTS_SCT_RF2_DISTRIBUTION_*.zip` in `WorkingFiles/`
- Extracts `Relationship_Snapshot` to `Files for upload/AMTv4/Terminology/`
- Extracts `SimpleMapSnapshot` to `Files for upload/AMTv4/Map/`
- Strips `_AUxxxx_xxxxxxxx` suffix from filenames
- Renames shortage files to `MedicineShortagesActiveResultSummaryExport.csv`

### Step 2: Filter SNOMED Change Report for Medicinal Products

```bash
python3 filter_medicinal_products.py
```

- Finds latest `SNOMEDCT-AU-concept-changes-*.csv` in `WorkingFiles/`
- Filters for `semantic_tag = "medicinal product"`
- Generates SNOMED URIs (`http://snomed.info/id/{concept_ID}`)
- Outputs `SNOMEDCT-AU-MedicinalProducts-YYYYMMDD-YYYYMMDD.csv`

### Step 3: Research International Codes

For each new Medicinal Product, research:

- **DrugBank ID**: https://go.drugbank.com/ (single substance MPs only, avoid acetate/phosphate variations - if in doubt, leave it out)
- **ATC Code**: https://www.whocc.no/atc_ddd_index/ (may have multiple codes, new drugs may not have one yet)
- **Pregnancy Category**: Check DrugBank or TGA databases
- **Beers Criteria**: Check American Geriatrics Society Beers Criteria (most new drugs not listed)

## Manual Workflow

### Input Files Required

Download and place in `WorkingFiles/`:
- NCTS Distribution Zip from [NCTS](https://www.healthterminologies.gov.au/access-clinical-terminology/access-snomed-ct-au/other/)
- Medicine Shortages CSV from TGA
- SNOMED CT-AU Change Report CSV from NCTS

### CSV/Excel Preparation

**Important**: If using Excel, format all cells as Text before pasting data. Excel corrupts AMT codes by converting large IDs to scientific notation.

### Update Australia Health Thesaurus (AHT)

Using PoolParty (Authoring environment):

1. Take a snapshot before editing
2. Add new concepts under Medicinal Products subtree:
   - Label in Sentence case (AMT4 standard)
   - Add `SNOMEDcode` and `SNOMED uri` attributes
   - Add DrugBank ID, ATC Code, Pregnancy Category, Beers Criteria as applicable
3. For Influenza Vaccines: maintain only current and previous year's MPs
4. Handle retired/inactive concepts:
   - **Retired, replaced**: Delete from AHT
   - **Inactive**: Update to target concept values, fix prefLabel case if old AMT3
5. Proofread, upload to SharePoint, save

## Directory Structure

- `WorkingFiles/` - Input directory for all source files (gitignored)
- `Files for upload/` - Output directory for processed files (gitignored)

## Data Formats

Output files are tab-separated RF2 (Release Format 2) SNOMED CT standard format.
