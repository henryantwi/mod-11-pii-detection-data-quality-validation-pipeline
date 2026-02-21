# Reflection on Data Quality & Governance (Refactored Pipeline)

## 1. Top 5 Data Quality Issues Found

During the exploratory analysis and validation of the `customers_raw.csv` dataset, the following critical issues were identified:

1.  **Column Misalignment (Structural Integrity)**
    -   **Issue:** Row 2 (`Jane Smith`) was missing the `address` field. Since the data was CSV (comma-separated), the lack of a placeholder caused subsequent columns (`income`, `account_status`, `created_date`) to shift left.
    -   **Fix:** In the `src/cleaning/cleaner.py` module, we implemented a heuristic to detect rows where `account_status` contains a date format. We then manually realigned the shifted values back into their correct columns.
    -   **Impact:** Corrects type mismatch errors downstream and ensures analytical components don't fail parsing numerical incomes out of string statuses.

2.  **Invalid Date Formats**
    -   **Issue:** Dates were inconsistent (`1990-07-22`, `01/15/2024`, `1975/05/10`) and included literal substrings like `invalid_date`.
    -   **Fix:** The Pydantic model (`src/validation/models.py`) uses a custom `@field_validator` via `strptime` to interpret multiple allowable layouts, unifying them to `YYYY-MM-DD`. `invalid_date` strings are caught as validation errors and scrubbed in the cleaning module.
    -   **Impact:** Ensures all temporal data is queryable and standard for cohort analysis.

3.  **Inconsistent Phone Formatting**
    -   **Issue:** Phone numbers appeared as `(555) 234-5678`, `555.789.0123`, `5557890123`, etc.
    -   **Fix:** The cleaner module strips all non-digit characters via regex and reformats exactly 10-digit numbers into `XXX-XXX-XXXX`. The validation layer ensures only strings with 7-15 digits are acceptable.
    -   **Impact:** Standardized communication layouts simplify integration with CRM systems.

4.  **Missing Mandatory Fields**
    -   **Issue:** Identifiers like `first_name` and `last_name` were null in some rows, along with `address` and `account_status`.
    -   **Fix:** The data cleaner fills text fields with placeholder identifiers (`[UNKNOWN]`, `[MISSING ADDRESS]`) and standardizes categorical nulls to `unknown`.
    -   **Impact:** Prevents Null Pointer Exceptions (NPEs) in analytics dashboards while flagging records for later enrichment.

5.  **Invalid Categorical Values & Negative Numerics**
    -   **Issue:** Income values and account statuses were invalid due to row misalignment.
    -   **Fix:** Implemented strict Pydantic `Literal` checks for `account_status` (`active`, `inactive`, `suspended`) and a ge/le bound on `income` (0 to 10,000,000) to catch these anomalies during validation.

## 2. PII Risk Assessment & Mitigation

Using the `src/pii/detector.py` module, we mapped fields to semantic categories.

*   **Identifiable (High Risk):** `first_name`, `last_name`, `email`, `phone`
*   **Sensitive Personal (High Risk):** `date_of_birth`, `address`
*   **Financial (Medium Risk):** `income`

**Detected Risks & Damage Potential:**
*   **Phishing & Social Engineering:** Full emails and phones expose customers to targeted scams.
*   **Identity Theft:** Providing Name + DOB + Address is a "full-z" profile used to originate fraudulent bank accounts.

## 3. Masking Trade-offs

Using `src/masking/masker.py`, we redacted PII. Masking protects privacy but reduces raw utility.

*   **Trade-off 1 (Emails):** Masking `john.doe@gmail.com` to `j***@gmail.com` prevents the marketing team from emailing the client but allows data analysts to group demographics by domain.
*   **Trade-off 2 (DOB):** Obscuring `1985-03-15` to `1985-**-**` means exact birthday campaigns are impossible, but age-bracket aggregations are still valid.
*   **Operational Context:** Data leaving the secure production boundary to data science sub-networks *must* be masked. Customer support teams viewing individual profiles via the core application *must not* be masked.

## 4. Validation Strategy: The Pydantic Advantage

The transition to Pydantic (`src/validation/models.py`) fundamentally improved the pipeline's robustness.

*   **Catch Rate:** Pydantic validators automatically caught typing issues, bounds failures (e.g., negative incomes), and ENUM mismatches in one pass without sprawling `if/else` statements.
*   **Misses & Improvements:** While Pydantic correctly flags the misaligned rows as invalid, it cannot automatically *fix* them (it's strictly a schema enforcer, not a transformer). The current pipeline relies on the cleaner module's heuristics to repair the rows. A future enhancement would be utilizing Great Expectations to measure the *drift* of these errors over time rather than simple row-level checks.

## 5. Production Operations

If deployed via Apache Airflow to run daily:
*   **Quarantine Layer:** Rows that fail the Pydantic validator (`val_data['failures']`) should be diverted to a Dead Letter Queue (DLQ) table in Snowflake/BigQuery for human review.
*   **Alerting:** If the run's fail count exceeds a 5% threshold, Slack alerts should trigger to the on-call Data Engineer, halting downstream dashboard refreshes.
*   **Success Path:** Only records that pass validation should enter the golden/curated layer for BI tools.

## 6. Lessons Learned

*   **Separation of Concerns:** Moving from a monolithic script to a folder-structured (`src/profiling`, `src/cleaning`, etc.) approach made the code infinitely more testable and readable.
*   **Validation First:** Pydantic makes validation declarative. Defining the schema object with constraints eliminates the chance of forgetting an edge case manually.
*   **The Misalignment Challenge:** Automated fixes for badly exported CSVs (like the missing comma in row 2) are incredibly fragile. Upstream governance (fixing the export query) is always preferred to downstream hacking.
