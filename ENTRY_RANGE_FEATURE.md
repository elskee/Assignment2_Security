# Entry Range Configuration Feature

## Overview

The vulnerability analysis script now supports flexible entry range configuration, allowing you to specify exactly which database entries to process.

## Configuration Methods

### Method 1: Environment Variable (.env file)

Add the `ENTRY_RANGE` variable to your `.env` file:

```env
# Process specific range
ENTRY_RANGE=1-10        # Entries 1-10
ENTRY_RANGE=26-51       # Entries 26-51 (default)
ENTRY_RANGE=100-200     # Entries 100-200

# Process all entries
ENTRY_RANGE=All
```

Then run without arguments:
```bash
python analyze_vulnerabilities.py
```

### Method 2: Command-Line Argument

Override the `.env` setting using the `--range` flag:

```bash
# Process entries 1-2
python analyze_vulnerabilities.py --range "1-2"

# Process entries 26-50
python analyze_vulnerabilities.py --range "26-50"

# Process all entries
python analyze_vulnerabilities.py --range "All"
```

## Usage Examples

### Quick Test (First 2 Entries)
```bash
python analyze_vulnerabilities.py --range "1-2"
```
**Time:** ~1 minute

### Original Assignment Range (Entries 26-51)
```bash
# Method 1: Set in .env
ENTRY_RANGE=26-51
python analyze_vulnerabilities.py

# Method 2: Command-line
python analyze_vulnerabilities.py --range "26-51"
```
**Time:** ~13 minutes

### First 10 Entries
```bash
python analyze_vulnerabilities.py --range "1-10"
```
**Time:** ~5 minutes

### Custom Range with Output File
```bash
python analyze_vulnerabilities.py --range "10-20" --output results_10_20.xlsx
```

### Process All Database Entries
```bash
python analyze_vulnerabilities.py --range "All"
```
**Time:** Depends on database size (could be hours for large databases)

## Test Mode Override

The `--test` flag always processes entries 1-2, regardless of `ENTRY_RANGE` setting:

```bash
python analyze_vulnerabilities.py --test
```

This is equivalent to `--range "1-2"` but more explicit for testing purposes.

## Priority Order

When multiple configurations are present, the priority is:

1. **`--test` flag** (highest priority) → Always processes entries 1-2
2. **`--range` argument** → Overrides .env setting
3. **`ENTRY_RANGE` from .env** → Used if no command-line argument
4. **Default value** (lowest priority) → "26-51" if nothing else specified

## Entry Range Format

### Specific Range
Format: `START-END` (inclusive, 1-based indexing)

Examples:
- `1-2` → First 2 entries
- `1-100` → First 100 entries
- `26-51` → Entries 26 through 51 (26 entries total)
- `50-150` → Entries 50 through 150 (101 entries total)

### All Entries
Format: `All` (case-insensitive)

Examples:
- `All`
- `all`
- `ALL`

## Error Handling

The script validates entry ranges and provides clear error messages:

```bash
# Invalid format
python analyze_vulnerabilities.py --range "abc"
# Error: Invalid entry range format: abc. Use format like '1-2', '26-50', or 'All'

# Invalid range (end < start)
python analyze_vulnerabilities.py --range "10-5"
# Error: End entry must be >= start entry

# Invalid start (< 1)
python analyze_vulnerabilities.py --range "0-10"
# Error: Start entry must be >= 1
```

## Output Information

The script displays the configured range at startup:

```
================================================================================
  ANALYSIS (Entries 26-51) - Starting Vulnerability Analysis
================================================================================

Connecting to database... [Processing entries 26-51]

Executing query...
[OK] Query returned 26 rows
```

## Performance Estimates

| Range | Entries | Approx. Time | API Calls | Estimated Cost |
|-------|---------|--------------|-----------|----------------|
| 1-2 | 2 | 1 min | 16 | $0.001 |
| 1-10 | 10 | 5 min | 80 | $0.01 |
| 26-51 | 26 | 13 min | 208 | $0.03 |
| 1-100 | 100 | 50 min | 800 | $0.12 |
| All | Variable | Variable | Variable | Variable |

*Cost estimates based on GPT-4o-mini pricing*

## Practical Use Cases

### 1. Quick Validation
```bash
# Test first 2 entries
python analyze_vulnerabilities.py --range "1-2"
```

### 2. Assignment Requirement (Entries 26-51)
```bash
# Set in .env: ENTRY_RANGE=26-51
python analyze_vulnerabilities.py
```

### 3. Batch Processing
```bash
# Process in chunks
python analyze_vulnerabilities.py --range "1-25" --output batch1.xlsx
python analyze_vulnerabilities.py --range "26-50" --output batch2.xlsx
python analyze_vulnerabilities.py --range "51-75" --output batch3.xlsx
```

### 4. Re-analyze Specific Entries
```bash
# Re-run entries that had errors
python analyze_vulnerabilities.py --range "15-20" --output rerun_15_20.xlsx
```

### 5. Complete Database Analysis
```bash
# Process everything
python analyze_vulnerabilities.py --range "All" --output complete_analysis.xlsx
```

## Technical Details

### SQL Query Construction

The script dynamically builds SQL queries based on the range:

**Specific Range (e.g., "26-51"):**
```sql
SELECT ... FROM (...) AS t
ORDER BY cve_id
LIMIT 26 OFFSET 25
```

**All Entries:**
```sql
SELECT ... FROM (...) AS t
ORDER BY cve_id
-- No LIMIT or OFFSET
```

### Range Parsing Logic

1. Read `ENTRY_RANGE` from .env (default: "26-51")
2. Override with `--range` if provided
3. Override with `--test` if provided (sets to "1-2")
4. Parse range string:
   - If "All": set OFFSET=0, LIMIT=None
   - If "X-Y": set OFFSET=X-1, LIMIT=Y-X+1
5. Construct and execute SQL query

## Migration from Previous Version

**Before (fixed range):**
```bash
# Only option was --test or default (26 entries)
python analyze_vulnerabilities.py
python analyze_vulnerabilities.py --test
```

**After (flexible range):**
```bash
# Many more options
python analyze_vulnerabilities.py --range "1-5"
python analyze_vulnerabilities.py --range "26-51"
python analyze_vulnerabilities.py --range "All"

# Or configure in .env
ENTRY_RANGE=26-51
python analyze_vulnerabilities.py
```

## Benefits

✅ **Flexibility**: Process any range of entries  
✅ **Cost Control**: Process small ranges for testing  
✅ **Batch Processing**: Split large analyses into chunks  
✅ **Re-analysis**: Re-run specific entries that failed  
✅ **Scalability**: Process entire database with "All"  
✅ **Convenience**: Set default range in .env  
✅ **Override**: Command-line always takes precedence  

## Notes

- Entry indices are 1-based (first entry is "1", not "0")
- Ranges are inclusive (both start and end are included)
- The `--test` flag is a convenience shortcut for `--range "1-2"`
- Processing "All" entries may take hours on large databases
- Consider API rate limits when processing many entries

