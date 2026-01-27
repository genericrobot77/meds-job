# ReferenceFiles

## Purpose

This folder stores **permanent reference documents and databases** that are used across multiple months of processing. Files in this folder are version-controlled in git and should never be deleted.

## What to Store Here

### Required Reference Files
- **Beers Criteria Spreadsheet** - American Geriatrics Society Beers Criteria for Potentially Inappropriate Medication Use in Older Adults
  - File: `Beers_Criteria_2025.csv`
  - **How it's used**: Research script automatically checks each new drug against this file
    - If drug's `prefLabel` matches an entry → `beers_criteria = "Listed"`
    - If not found → `beers_criteria = "Not listed"`
  - Format required: CSV with columns `prefLabel`, `Beers`, `ATCcode`
  - Update annually with new editions

- **TGA Pregnancy Category Database** - Australian categorisation for prescribing medicines in pregnancy
  - Reference: https://www.tga.gov.au/prescribing-medicines-pregnancy-database
  - Store periodic snapshots or export copies

### Optional Reference Files
- Drug reference databases (WHO, FDA, etc.)
- Historical research documents
- Lookup tables for drug classifications
- Previous month's reference documents for comparison

## Folder Rules

✅ **DO:**
- Add reference files you download
- Create subfolders for organization (e.g., `Beers_Criteria/`, `Pregnancy_Categories/`)
- Version dated files (e.g., `Beers_Criteria_2025-01.xlsx`)
- Commit changes to git

❌ **DON'T:**
- Delete files without good reason
- Store temporary monthly data (use WorkingFiles/ instead)
- Store large generated output files (use Files for upload/ instead)

## Usage in Scripts

When you have reference files stored here, update scripts to reference:
```
ReferenceFiles/filename
```

## Git Tracking

All files in this folder are tracked by git (unlike WorkingFiles/ and Files for upload/). This means:
- Files are backed up in version control
- You can see history of changes
- Files persist across months
- You can revert changes if needed
