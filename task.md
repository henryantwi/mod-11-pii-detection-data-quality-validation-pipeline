```markdown
# Module Lab: PII Detection & Data Quality Validation Pipeline Lab

**Data Engineering Mini Project**

---

## Overview

You've joined a fintech company that just collected customer data from multiple sources. It's messy and contains sensitive information.

**Your job:** Build a Python pipeline to profile the data, detect PII, validate quality, and remediate issues.

This is real work—data engineers spend ~40% of their time cleaning data before analysis.

---

## The Dataset

You have a CSV file: `customers_raw.csv`

```text
customer_id, first_name, last_name, email, phone, date_of_birth, address, income, account_status, created_date
1, John, Doe, john.doe@gmail.com, 555-123-4567,1985-03-15,123 Main St New York NY 10001,75000, active, 2024-01-10
2, Jane, Smith,jane.smith@company.com, 555-987-6543, 1990-07-22, 95000, active, 2024-01-11
3,, Johnson, bob.johnson@email.com,(555) 234-5678,1988-11-08,456 Oak Ave Los Angeles CA 90001,, suspended, 2024-01-12
4, Mary, Brown,mary.brown@gmail.com,555-345-6789,1975/05/10,789 Pine Rd Chicago IL 60601, 120000,,2024-01-13
5, Robert,, robert.wilson@yahoo.com,555-456-7890,2005-12-25,892 Elm St Houston TX 77001, 55000, active, 01/15/2024
6, Patricia, Davis, PATRICIA.DAVIS@GMAIL.COM, 555-567-8901, invalid_date, 101 Birch Ln Phoenix AZ 85001,82000, active, 2024-01-16
7, Michael, Miller, michael.miller@work.com, 555-678-9012, 1992-02-14,111 Maple Dr Philadelphia PA 19101,98000, active, 2024-01-17
8, Sarah, wilson, sarah.wilson@gmail.com, 555.789.0123, 1968-06-18, 121 Cedar way San Antonio TX 78201, 105000, inactive, 2024-01-18
9, David, Moore, david_moore@hotmail.com, 5557890123, 1958-09-30,,110000, active, 2024-01-19
10, Jennifer, Taylor, jennifer.taylor@company.net, 555-890-1234, 1970-03-05,131 Spruce St San Diego CA 92101,88000, active, invalid_date
```

---

## Expected Schema

| Column          | Type    | Rules                                          |
|----------------|---------|------------------------------------------------|
| customer_id     | Integer | Unique, positive                               |
| first_name      | String  | Non-empty, 2-50 chars, alphabetic             |
| last_name       | String  | Non-empty, 2-50 chars, alphabetic             |
| email           | String  | Valid email format                             |
| phone           | String  | Valid phone (normalize format)                 |
| date_of_birth   | Date    | Valid date, YYYY-MM-DD                         |
| address         | String  | Non-empty, 10-200 chars                        |
| income          | Numeric | Non-negative, ≤ 10M                            |
| account_status  | String  | Must be: 'active', 'inactive', 'suspended'    |
| created_date    | Date    | Valid date, YYYY-MM-DD                         |

---

## Part 1: Exploratory Data Quality Analysis

**Objective:** Profile the raw data to understand what's broken.

### Tasks

Load the CSV and investigate:

1. **Completeness** — Which columns have missing values? (Report as %)
2. **Data types** — Are columns the correct type? (e.g., is `date_of_birth` a string or datetime?)
3. **Format issues** — What phone formats exist? What date formats?
4. **Uniqueness** — Is `customer_id` truly unique?
5. **Invalid values** — Are there dates like `invalid_date`? Negative incomes? Ages > 150?
6. **Categorical validity** — Does `account_status` only contain valid values?

### Deliverable: `data_quality_report.txt`

Write a report with:

- Completeness % per column  
- Data types detected  
- List of quality issues found (with examples)  
- Estimated impact (e.g., "5 rows have missing addresses = 50% incomplete")

**Format example:**

```text
DATA QUALITY PROFILE REPORT
===========================

COMPLETENESS:
- customer_id: 100%
- first_name: 90% (1 missing)
- last_name: 90% (1 missing)
...

DATA TYPES:
- customer_id: INT ✓
- first_name: STRING ✓
- date_of_birth: STRING X (should be DATE)

QUALITY ISSUES:
1. [Issue], Examples: [show rows]
2. [Issue], Examples: [show rows]

SEVERITY:
- Critical (blocks processing): X
- High (data incorrect): Y
- Medium (needs cleaning): Z
```

---

## Part 2: Detect PII

**Objective:** Identify personally identifiable information.

### Tasks

1. **Identify which columns contain PII:**
   - Names (`first_name`, `last_name`)
   - Contact info (`email`, `phone`)
   - Sensitive personal data (`date_of_birth`, `address`)

2. **Write a PII detector that finds patterns in the data:**
   - Use regex to find email patterns (format: `something@domain.com`)
   - Use regex to find phone patterns (format: `XXX-XXX-XXXX` or variations)
   - Identify rows where PII is exposed

3. **Quantify the risk:**
   - How many rows contain email addresses?
   - How many contain phone numbers?
   - What if this data was breached?

### Deliverable: `pii_detection_report.txt`

**Format example:**

```text
PII DETECTION REPORT
======================

RISK ASSESSMENT:
- HIGH: Names, emails, phone numbers, addresses, dates of birth
- MEDIUM: Income (financial sensitivity)

DETECTED PII:
- Emails found: 10 (100%)
- Phone numbers found: 10 (100%)
- Addresses found: 8 (80%)
- Dates of birth found: 9 (90%)

EXPOSURE RISK:
If this dataset were breached, attackers could:
- Phish customers (have emails)
- Spoof identities (have names + DOB + address)
- Social engineer (have phone numbers)

MITIGATION:
Mask all PII before sharing with analytics teams
```

---

## Part 3: Build a Data Validator

**Objective:** Define and apply validation rules.

### Tasks

1. **Choose a validation library:** Pandera, Pydantic, or Great Expectations (or write custom)

2. **Define validation rules for each column:**
   - `customer_id`: unique, positive integer
   - `first_name`, `last_name`: non-null, letters only, 2-50 chars
   - `email`: valid email format
   - `phone`: reasonable length
   - `date_of_birth`, `created_date`: valid dates
   - `account_status`: only valid values
   - `income`: non-negative, ≤ 10M

3. **Run validation** against the raw data and capture failures

4. **Document failures:**
   - Which rows failed?
   - Which columns had issues?
   - What was wrong?  

### Deliverable: `validation_results.txt`

**Format example:**

```text
VALIDATION RESULTS
==================

PASS: [X rows passed all checks]
FAIL: [Y rows failed]

FAILURES BY COLUMN:
-------------------
first_name:
- Row 3: Empty (should be non-empty)
- Row 6: 'PATRICIA' (should be title case after cleaning)

date_of_birth:
- Row 5: '01/15/2024' (wrong format, should be YYYY-MM-DD)
- Row 6: 'invalid_date' (invalid date value)
- Row 10: 'invalid_date' (invalid date value)

account_status:
- Row 4: Empty (should be one of: active, inactive, suspended)
- Row 13: 'unknown' (invalid value)

phone:
- Row 8: '555.789.0123' (non-standard format, should be XXX-XXX-XXXX)
- Row 9: '5557890123' (no formatting)
...
```

---

## Part 4: Clean the Data

**Objective:** Fix data quality issues.

### Tasks

1. **Normalize formats:**
   - Phone numbers: Convert all to `XXX-XXX-XXXX` format
   - Dates: Convert all to `YYYY-MM-DD` format
   - Names: Apply title case (first letter uppercase)

2. **Handle missing values:**
   - Decide: delete row, fill with placeholder, or flag for review
   - Document your strategy

3. **Validate after cleaning:** Re-run validators to confirm fixes

4. **Output cleaned data:** Save to `customers_cleaned.csv`

### Deliverable: `cleaning_log.txt`

**Format example:**

```text
DATA CLEANING LOG
=================

ACTIONS TAKEN:
--------------

Normalization:
- Phone format: Converted 4 formats -> XXX-XXX-XXXX (3 rows affected)
- Date format: Converted 2 formats -> YYYY-MM-DD (5 rows affected)
- Name case: Applied title case to PATRICIA (1 row affected)

Missing Values:
- first_name: 1 row missing -> filled with '[UNKNOWN]'
- last_name: 1 row missing -> filled with '[UNKNOWN]'
- address: 2 rows missing -> filled with '[UNKNOWN]'
- income: 1 row missing -> filled with 0
- account_status: 1 row missing -> filled with 'unknown'

Validation After Cleaning:
- Before: 3 rows failed
- After: 0 rows failed
- Status: PASS

Output:
customers_cleaned.csv (10 rows, 10 columns)
```

---

## Part 5: Mask PII

**Objective:** Protect sensitive data before sharing.

### Tasks

1. **Implement masking functions** that hide PII but preserve data structure:
   - Names: `John Doe` → `J*** D***`
   - Emails: `john.doe@gmail.com` → `j***@gmail.com`
   - Phone: `555-123-4567` → `***-***-4567`
   - Addresses: `123 Main St` → `[MASKED ADDRESS]`
   - DOB: `1985-03-15` → `1985-**-**`

2. **Apply masking** to cleaned data

3. **Save masked dataset:** `customers_masked.csv`

4. **Compare before/after:**
   - Original: Full PII visible
   - Masked: Sensitive data hidden, but data structure intact  

### Deliverable: `masked_sample.txt`

**Format example:**

```text
BEFORE MASKING (first 2 rows):
------------------------------
customer_id, first_name, last_name, email, phone, date_of_birth, address, income, account_status, created_date
1, John, Doe, john.doe@gmail.com, 555-123-4567,1985-03-15,123 Main St New York NY 10001, 75000, active, 2024-01-10
2, Jane, Smith,jane.smith@company.com, 555-987-6543, 1990-07-22,456 Oak Ave Los Angeles CA 90001, 95000, active, 2024-01-11

AFTER MASKING (first 2 rows):
-----------------------------
customer_id, first_name, last_name, email, phone, date_of_birth, address, income, account_status, created_date
1, J***, D***, j***@gmail.com, ***-***-4567, 1985-**-**, [MASKED ADDRESS], 75000, active, 2024-01-10
2, J***, S***, j***@company.com, ***-***-6543, 1990-**-**, [MASKED ADDRESS], 95000, active, 2024-01-11

ANALYSIS:
- Data structure preserved (still 10 rows, 10 columns)
- PII masked (names, emails, phones, addresses, DOBs hidden)
- Business data intact (income, account_status, dates available)
- Use case: Safe for analytics team (GDPR compliant)
```

---

## Part 6: Build an End-to-End Pipeline

**Objective:** Orchestrate all steps into a single automated workflow.

### Tasks

1. **Create a main pipeline script that:**
   - Loads raw data
   - Cleans data (normalize formats, handle missing values)
   - Validates against rules
   - Detects PII
   - Masks PII
   - Saves cleaned, masked output
   - Generates report

2. **Structure the code:**
   - Separate functions/classes for each step
   - Error handling (what if validation fails?)
   - Logging (track what happened)
   - Documentation (why each step exists)

3. **Make it production-ready:**
   - Input: raw CSV file
   - Output: cleaned CSV + reports
   - Should run without manual intervention  

### Deliverable: `pipeline_execution_report.txt`

**Format example:**

```text
PIPELINE EXECUTION REPORT
=========================

Timestamp: 2024-01-20 10:30:00

Stage 1: LOAD
✓ Loaded customers_raw.csv - 10 rows, 10 columns

Stage 2: CLEAN
✓ Normalized phone formats (3 rows)
✓ Normalized date formats (5 rows)
✓ Fixed capitalization (1 row)
✓ Filled missing values (5 rows)

Stage 3: VALIDATE
✓ Passed schema validation
- customer_id: 10/10 unique
- first_name: 10/10 non-null
- email: 10/10 valid format
... (all passed)

Stage 4: DETECT PII
✓ Found PII in:
- 10 email addresses
- 10 phone numbers
- 8 addresses
- 9 dates of birth

Stage 5: MASK
✓ Masked all PII
- Names: masked
- Emails: masked
- Phones: masked
- Addresses: masked
- DOBs: masked

Stage 6: SAVE
✓ Saved outputs:
- customers_cleaned.csv (masked data)
- data_quality_report.txt
- validation_results.txt
- pii_detection_report.txt

SUMMARY:
- Input: 10 rows (messy)
- Output: 10 rows (clean, masked, validated)
- Quality: PASS
- PII Risk: MITIGATED (all masked)

Status: SUCCESS ✓
```

---

## Part 7: Reflection & Governance

**Objective:** Think critically about data quality, privacy, and operations.

Write a 1–2 page reflection addressing:

### 1. What were the biggest data quality issues?
   - List top 5 problems found
   - How did you fix each?
   - What was the impact?

### 2. PII Risk Assessment
   - What PII did you detect?
   - Why is it sensitive?
   - What damage could occur if leaked?

### 3. Masking Trade-offs
   - By masking PII, you reduced data utility
   - Example: Can't contact customers (emails masked)
   - When is masking worth the trade-off?
   - When would you NOT mask?

### 4. Validation Strategy
   - Did your validators catch all issues?
   - What did they miss?
   - How would you improve them?

### 5. Production Operations
   - How would this pipeline run in real life?
   - Daily? Hourly? On-demand?
   - What happens if validation fails?
   - Who gets notified?
   - How do you handle failures?

### 6. Lessons Learned
   - What surprised you?
   - What was harder than expected?
   - What would you do differently next time?  

---

## Deliverables Checklist

- ☐ Part 1: `data_quality_report.txt` (profiling results)
- ☐ Part 2: `pii_detection_report.txt` (what PII was found)
- ☐ Part 3: `validation_results.txt` (which rows failed validation)
- ☐ Part 4: `cleaning_log.txt` (what was fixed)
- ☐ Part 5: `masked_sample.txt` (before/after comparison)
- ☐ Part 6: `pipeline_execution_report.txt` (end-to-end summary)
- ☐ Part 6: `customers_cleaned.csv` (output data file)
- ☐ Part 7: `reflection.md` (1–2 page analysis)
- ☐ Python code files (pipeline, validators, maskers, etc.)

---

## Key Concepts

- ✓ Data profiling & quality assessment
- ✓ PII detection & masking
- ✓ Data validation rules
- ✓ ETL pipeline design
- ✓ Production-ready code structure  
- ✓ Governance & compliance thinking  
```