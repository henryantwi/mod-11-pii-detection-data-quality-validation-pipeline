# Reflection on Data Quality & Governance

## 1. Top 5 Data Quality Issues Found

During the exploratory analysis and validation of the `customers_raw.csv` dataset, the following critical issues were identified:

1.  **Column Misalignment (Structural Integrity)**
    -   **Issue:** Row 2 (Jane Smith) had a missing value for `address`, causing subsequent columns (`income`, `account_status`, `created_date`) to shift left. This resulted in data landing in incorrect columns (e.g., "active" appearing in the `income` column).
    -   **Fix:** Detected rows where `account_status` contained a date pattern. Applied a corrective shift logic: moved values to their correct columns and set the missing `address` to `NaN`.
    -   **Impact:** Without this fix, downstream analytics would have failed due to type mismatches (string in numeric field) and incorrect status reporting.

2.  **Invalid Date Formats**
    -   **Issue:** Dates were inconsistent, appearing as `YYYY-MM-DD` (standard), `YYYY/MM/DD`, `MM/DD/YYYY`, and the string literal `invalid_date`.
    -   **Fix:** Implemented a parser that attempted multiple format patterns. Values like `invalid_date` were coerced to `NaN` (or a default placeholder).
    -   **Impact:** Ensures all temporal data is queryable and sortable.

3.  **Inconsistent Formatting**
    -   **Issue:** Phone numbers appeared in various formats (`(555) ...`, `555-...`, `555.789...`, unformatted). Names had inconsistent capitalization (`PATRICIA` vs `John`).
    -   **Fix:** Normalized phone numbers to `XXX-XXX-XXXX` by stripping non-digits. Applied Title Case to names.
    -   **Impact:** Improved matching and deduplication capabilities.

4.  **Missing Mandatory Fields**
    -   **Issue:** Critical identifiers like `first_name` and `last_name` were missing in some rows. `Account_status` and `Address` were also missing.
    -   **Fix:** Filled missing text fields with `[UNKNOWN]` or `[MISSING...]` and numeric fields with `0` or default values.
    -   **Impact:** Prevented null pointer exceptions in applications but flagged these records for manual review.

5.  **Invalid Categorical values**
    -   **Issue:** `account_status` contained `nan` or incorrect values due to shifting.
    -   **Fix:** After realignment, missing statuses were set to `unknown`.
    -   **Impact:** Maintained referential integrity for status codes.

## 2. PII Risk Assessment

The dataset contained significant PII, categorized by sensitivity:

*   **Identifiable PII (High Risk):** `first_name`, `last_name`, `email`, `phone`, `account_status` (contextual).
*   **Sensitive PII (High Risk):** `date_of_birth`, `address`.
*   **Financial PII (Medium Risk):** `income`.

**Detectd Risks:**
*   **Phishing:** 100% of rows contained email addresses, making customers vulnerable to targeted attacks.
*   **Identity Theft:** The combination of Full Name + DOB + Address is sufficient for high-level identity theft (e.g., opening fraudulent accounts).
*   **Social Engineering:** Phone numbers coupled with account details allow attackers to impersonate support staff.

## 3. Masking Trade-offs

Masking protects user privacy but reduces data utility for some stakeholders.

*   **Trade-off:** Masking emails (`j***@gmail.com`) prevents the marketing team from sending campaigns but allows analysts to aggregate by domain (e.g., count of Gmail users).
*   **Trade-off:** Masking dates of birth (`1985-**-**`) prevents exact age calculation but allows for age-bracket analysis (e.g., cohort analysis).
*   **When to Mask:** Always mask PII when data leaves the production/OLTP environment for analytics, testing, or third-party sharing.
*   **When NOT to Mask:** Customer Support systems (authorized personnel) need full visibility to verify identity and contact users.

## 4. Validation Strategy

*   **Performance:** The validators successfully caught structural issues (misalignment via type checks), format errors (dates, phones), and missing values.
*   **Misses:** Initial validators missed the logic error where `income` was "active" because strict type checking wasn't applied to all fields initially. Adding bounds checks (min/max income) improved this.
*   **Improvement:** Implementing looking-ahead validation (e.g., if column N is "active", check if column N-1 is an address pattern) could automate the realignment fix rather than relying on a hardcoded rule.

## 5. Production Operations

*   **Schedule:** Run daily (batch) after data ingestion.
*   **Failure Handling:**
    *   **Data Quality (DQ) Gate:** If >10% of rows fail validation, halt the pipeline and alert the Data Engineering team.
    *   **Row-Level Quarantine:** For minor failures (<10%), quarantine bad rows to a "dead letter queue" table for manual review, while processing the clean rows.
*   **Notifications:** Slack/Email alerts with the `pipeline_execution_report.txt` attached.

## 6. Lessons Learned

*   **Surprise:** How a single missing comma or value (like the missing address in Row 2) can corrupt disparate columns downstream. It emphasizes the need for robust parsing or schema validation *before* loading.
*   **Challenge:** Generalizing the "fix" for misaligned data is hard. The heuristic used here (checking if `account_status` looks like a date) works for this specific mess but might be fragile in real-world scenarios with random noise.
*   **Future:** Use a library like `Great Expectations` for more declarative validation rules and data docs.
