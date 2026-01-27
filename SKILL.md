---
name: NCTS Data Processing
description: Automates the processing of NCTS distribution zip files, Medicine Shortages CSVs, and SNOMED CT-AU change reports with international code research.
---

# NCTS Data Processing

This skill automates the extraction and organization of NCTS (National Clinical Terminology Service) data files, Medicine Shortages reports, and SNOMED CT-AU change reports. It includes automated international code research for new medicinal products.

## Prerequisites

1.  **Python 3**: Ensure Python 3 is installed.
2.  **Monthly Input Files** (place in `WorkingFiles` directory - delete after processing):
    *   **NCTS Distribution Zip** (e.g., `NCTS_SCT_RF2_DISTRIBUTION_*.zip`)
    *   **Medicine Shortages** file (e.g., `*Shortages*.csv`)
    *   **SNOMED CT-AU Change Report** (e.g., `SNOMEDCT-AU-concept-changes-*.csv`)
3.  **Optional Reference Files** (place in `ReferenceFiles` directory - permanent):
    *   Pregnancy category reference spreadsheets
    *   Drug reference databases
    *   Other permanent reference materials

## Automated Workflow

This is the **monthly automated workflow** that processes all three input files:

### Step 1: Process NCTS Files and Medicine Shortages

Run the NCTS processing script:

```bash
python3 process_ncts_data.py
```

**What it does:**
1.  **Setup Directories**: Checks/creates `Files for upload/AMTv4/Terminology` and `Files for upload/AMTv4/Map`
2.  **Process NCTS Zip**:
    *   Finds the latest NCTS zip in `WorkingFiles`
    *   Extracts it temporarily
    *   Copies `Relationship_Snapshot` to `Files for upload` and renames it
    *   Copies `SimpleMapSnapshot` to `Files for upload` and renames it
3.  **Process Shortages**:
    *   Finds the shortages CSV/XLS in `WorkingFiles`
    *   Renames it to `MedicineShortagesActiveResultSummaryExport.csv`

### Step 2: Filter SNOMED Change Report for Medicinal Products

Run the filtering script:

```bash
python3 filter_medicinal_products.py
```

**What it does:**
1.  Reads the SNOMED CT-AU change report CSV from `WorkingFiles`
2.  Filters for entries with `semantic_tag = "medicinal product"`
3.  Generates SNOMED URIs by appending concept IDs to `http://snomed.info/id/`
4.  Creates output file: `SNOMEDCT-AU-MedicinalProducts-YYYYMMDD-YYYYMMDD.csv`
5.  Displays summary of Medicinal Products found

**Output includes:**
- All original columns from the change report
- New `SNOMED_uri` column (placed after `concept_ID`)

### Step 3: Research International Codes

Run the research script to choose your research method:

```bash
python3 research_medicinal_products.py
```

**Research Mode Comparison:**

| Mode | Command | Use For | Success Rate | Cost |
|------|---------|---------|--------------|------|
| **Interactive + Direct Sites** | `--interactive` | Most codes (DrugBank, Pregnancy) | ⭐⭐⭐ Good | None |
| **Web Search for ATC** | `--search-atc "Drug"` | Missing ATC codes | ⭐⭐⭐ Good | Tokens |
| **Antigravity Agent** | `--antigravity` | Full automation | ⭐⭐⭐ Best | Quota-based |
| **Claude WebFetch** | `--claude` | Fallback | ⭐⭐ Limited | Tokens |

**Recommended Workflow:**

1. **Start with Interactive Mode:**
   ```bash
   python3 research_medicinal_products.py --interactive
   ```
   → Guided step-by-step entry with direct website links
   → Try https://atcddd.fhi.no/atc_ddd_index/ first for ATC codes
   → Saves progress after each product

2. **If ATC Code Not Found on Direct Site:**
   ```bash
   python3 research_medicinal_products.py --search-atc "Drug Name"
   ```
   → Claude searches web for the missing ATC code
   → Copy results back into `research_data.json`

3. **When Antigravity Quota Available:**
   ```bash
   python3 research_medicinal_products.py --antigravity
   ```
   → Use for comprehensive browser automation
   → Copy prompt to Antigravity Agent
   → Paste results into `research_data.json`

4. **Generate Reference Document:**
   ```bash
   python3 research_medicinal_products.py --generate
   ```
   → Creates `MedicinalProducts-Research-YYYYMMDD-YYYYMMDD.csv`
   → Ready for AHT updates in PoolParty

**Why Interactive Mode is Good:**
- Direct access to websites while entering data
- Can click links provided by script
- Self-paced - skip products and come back
- No token cost
- Validation tips built into prompts

**Interactive Mode Features:**
- Detailed prompts for each field with examples
- Direct links to all research websites
- Progress tracking (e.g., "[2/4]")
- Skip ('s') or quit ('q') options
- Clear formatting and guidance

**Research Data Collected:**

| Field | Source | Required? |
|-------|--------|-----------|
| DrugBank ID | https://go.drugbank.com/ | Single-substance drugs only |
| ATC Code(s) | https://atcddd.fhi.no/atc_ddd_index/ | When available |
| Pregnancy Category (AU) | https://www.tga.gov.au/prescribing-medicines-pregnancy-database | Optional |
| Pregnancy Category (FDA) | FDA labeling | Optional |
| Beers Criteria | AGS Beers Criteria | Optional (usually "Not listed") |
| Clinical Notes | Any reliable source | Recommended |

**Output Files:**
- `WorkingFiles/research_data.json` - Structured research data
- `WorkingFiles/MedicinalProducts-Research-YYYYMMDD-YYYYMMDD.csv` - Reference document for AHT

## Manual Workflow: SNOMED CT-AU & AHT Update

### 1. Download SNOMED CT-AU Change Reports
1.  **Go to NCTS**: Visit [SNOMED CT-AU > Other](https://www.healthterminologies.gov.au/access-clinical-terminology/access-snomed-ct-au/other/).
2.  **Download**: Select the **DOWNLOAD as CSV** option.
3.  **Locate File**: The file will be the SNOMED CT-AU Change Reports (CSV).
4.  **Place in WorkingFiles**: Move the downloaded file to the `WorkingFiles` directory.

### 2. CSV/Excel Preparation
> [!IMPORTANT]
> If using Excel, you MUST format columns as text before pasting data. Excel may corrupt AMT codes (e.g., converting large IDs to scientific notation).

1.  **Open in Text Editor**: Open the downloaded file in a text editor (e.g., Notepad++, VS Code, Sublime Text).
2.  **Prepare Excel**:
    -   Open a new Excel spreadsheet.
    -   **Select all cells** and format as **Text**.
3.  **Import Data**: Copy the data from the text editor into the prepared spreadsheet.
    -   Use **Text to Columns** if necessary to separate elements.
4.  **Verify**: Check that AMT codes (`concept_ID` column) are correct and not corrupted.
5.  **Filter**: The automated script has already filtered for Medicinal Products.

### 3. Update Australia Health Thesaurus (AHT)
**Tool**: PoolParty (Authoring environment)

1.  **Snapshot**: Take a snapshot of the AHT project before editing.
2.  **Add New Concepts**:
    -   In the **Medicinal Products** subtree, create a new concept for each identified MP.
    -   **Label**: Use Sentence case (AMT4 standard).
    -   **Attributes**:
        -   Add `SNOMEDcode` (from the `concept_ID` column)
        -   Add `SNOMED uri` (from the `SNOMED_uri` column generated by script)
    -   **Influenza Vaccines**: Maintain only current and previous year's MPs. (e.g., if adding 2025, delete 2023)

#### Additional Attributes
*   **Pregnancy Category**: Add if applicable (from research).
*   **Beers Criteria**: Add if applicable (from research).
*   **DrugBank ID**: Add if applicable (from research).
    -   Only use for **single substance** MPs (exclude variations like acetate/phosphate).
    -   *If in doubt, leave it out.*
*   **ATC Code**: Add if applicable (from research).
    -   Note: MPs may be listed under slightly different names.
    -   Several codes may exist for one MP.
    -   New drugs may not have codes yet.

#### Related Concepts
*   Add relations mainly for **drug classes**.
*   Use ATC code as a guideline.
*   Avoid relating to specific diseases unless clearly associated.

### 4. Handle Retired/Inactive Concepts
*   **Retired, replaced**: Delete the retired concept from AHT if found.
*   **Inactive**:
    -   Change the `concept_id` and `snomed uri` to the `target_concept_preferred_term` SNOMED value.
    -   Update `prefLabel` to sentence case if it was an old lowercase AMT3 MP.

### 5. Finalisation
1.  **Proofread**: Check all changes.
2.  **Upload**: Upload the working file to the "Info Mgt Folder" in SharePoint.
3.  **Save**: Save the Working file when satisfied.

## Monthly Workflow Summary

1.  **Download** (Manual):
    - NCTS Distribution Zip from NCTS
    - Medicine Shortages CSV from TGA
    - SNOMED CT-AU Change Report from NCTS
    - Place all files in `WorkingFiles` directory

2.  **Process** (Automated):
    - Run `process_ncts_data.py` for NCTS and Shortages files
    - Run `filter_medicinal_products.py` for SNOMED change report

3.  **Research** (Automated):
    - Run `python3 research_medicinal_products.py` to initialize research
    - **Beers Criteria** - Automatically checked against `ReferenceFiles/Beers_Criteria_2025.csv`
      - If drug name matches prefLabel in reference file → flagged as "Listed"
      - If not found → "Not listed" (correct for new drugs)
    - Run with research mode:
      - `--claude` - Web search for DrugBank, ATC codes, Pregnancy Category
      - `--antigravity` - Full browser automation for all codes
      - `--interactive` - Manual entry with guided prompts
    - Reference document auto-generated in WorkingFiles/

4.  **Update AHT** (Manual):
    - Import concepts into PoolParty
    - Add all required and optional attributes
    - Handle retired/inactive concepts
    - Proofread and save

## Folder Structure

### WorkingFiles/ (Monthly - Cleared After Processing)
- **Purpose**: Temporary input directory for monthly downloads
- **Contains**:
  - NCTS_SCT_RF2_DISTRIBUTION_*.zip
  - SNOMEDCT-AU-concept-changes-*.csv
  - Medicine Shortages CSV/Excel
- **Action**: Delete all contents after each month's processing

### Files for upload/ (Monthly - Cleared After Processing)
- **Purpose**: Temporary output directory for processed files
- **Contains**:
  - Relationship_Snapshot files (Terminology/)
  - SimpleMapSnapshot files (Map/)
  - Renamed shortages files
- **Action**: Upload to SharePoint, then delete contents after each month

### ReferenceFiles/ (Permanent - Tracked in Git)
- **Purpose**: Store permanent reference files and databases
- **Keep files here**:
  - Beers Criteria Excel spreadsheet
  - Pregnancy category lookup files
  - Drug reference databases
  - Historical AHT research documents
  - Any other reference materials needed across multiple months
- **Action**: Keep files permanently, commit changes to git
- **Note**: Files added here will be version-controlled and preserved
