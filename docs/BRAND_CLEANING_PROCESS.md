# Brand Master System & Cleaning Process

## Overview
This document describes the **Brand Master** system, a robust data governance layer designed to resolve inconsistent brand names in the ASOS dataset. We moved from a simple `dim_brand` text lookup to a canonical **Master-Alias** model.

## The Problem
The raw product data contained:
1.  **Dirty Names**: *"New Look boxy gilet"* (Product Title) vs *"New Look"* (Brand).
2.  **Duplicates**: *"Adidas"*, *"adidas"*, *"ADIDAS"* treated as different entities.
3.  **Ambiguity**: *"ASOS DESIGN"* vs *"ASOS"*.

## The Solution: Brand Master Schema
We implemented a **Hybrid Schema** where `dim_product` links to a `brand_master_id`.

### Tables
1.  **`brand_master`**: The "Gold Standard" or Canonical names.
    *   *Columns*: `brand_master_id`, `brand_canonical`, `is_sub_brand`.
2.  **`brand_alias`**: Maps variations to the master.
    *   *Columns*: `alias_id`, `brand_master_id`, `alias_text` (e.g., "adidas" -> Master "Adidas").

---

## The Cleaning Pipeline

The process consists of three distinct steps:

### 1. Extraction (Heuristic)
**Script**: `fix_brands.py`
*   **Goal**: specific brand candidates from raw product titles.
*   **Logic**: Heuristic extraction (Title Case / Uppercase words at start of string).
*   **Output**: Populates the legacy `dim_brand` table with candidate string.

### 2. Population (Clustering & Linking)
**Script**: `src/populate_brand_master.py`
*   **Goal**: Create Canonical Masters and link products.
*   **Logic**:
    *   **Normalization**: Lowercase, remove special chars.
    *   **Fuzzy Clustering**: Uses `rapidfuzz` (Levenshtein Distance > 90%) to group variations.
    *   **Canonical Selection**: Picks the best casing (e.g., "Nike" over "nike").
    *   **Safe Linking**: Unlinks products, populates `brand_master` & `brand_alias`, then updates `dim_product` with `brand_master_id`.

### 3. Verification
**Script**: `src/analysis/verify_brand_master.py`
*   **Goal**: Ensure data quality constraints.
*   **Checks**:
    *   Zero normalized duplicates in Master.
    *   Specific rule: ASOS family separation ("ASOS" != "ASOS DESIGN").
    *   Coverage: >95% of products must be linked.

---

## Usage / Maintenance

If raw data is re-ingested, run the full pipeline:

```bash
# 1. Extract Candidates
python fix_brands.py

# 2. Build Master & Link
python -m src.populate_brand_master

# 3. Verify
python src/analysis/verify_brand_master.py
```

## Files Involved
*   `fix_brands.py`: Initial extraction.
*   `src/populate_brand_master.py`: Clustering and Master population.
*   `src/analysis/verify_brand_master.py`: Quality checks.
*   `src/utils/db_utils.py`: Database connection helpers.
