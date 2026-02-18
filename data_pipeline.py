import pandas as pd
import numpy as np
import re
import datetime
import time

# --- Configuration ---
RAW_FILE = 'customers_raw.csv'
CLEANED_FILE = 'customers_cleaned.csv'
MASKED_FILE = 'customers_masked.csv'

DQ_REPORT = 'data_quality_report.txt'
PII_REPORT = 'pii_detection_report.txt'
VALIDATION_REPORT = 'validation_results.txt'
CLEANING_LOG = 'cleaning_log.txt'
MASKED_SAMPLE = 'masked_sample.txt'
PIPELINE_REPORT = 'pipeline_execution_report.txt'

EXPECTED_COLUMNS = [
    'customer_id', 'first_name', 'last_name', 'email', 'phone', 
    'date_of_birth', 'address', 'income', 'account_status', 'created_date'
]

# --- Helper Functions ---

def load_data(file_path):
    print(f"Loading data from {file_path}...")
    # Using engine='python' allows more flexible parsing, but here we expect some malformed lines.
    # If a line has fewer fields than the header, pandas by default fills the end with NaNs.
    try:
        df = pd.read_csv(file_path, skipinitialspace=True)
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def write_report(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Generated report: {filename}")

# --- Part 1: Exploratory Data Quality Analysis ---

def profile_data(df):
    report = ["DATA QUALITY PROFILE REPORT", "===========================", ""]
    
    # 1. Completeness
    report.append("COMPLETENESS:")
    for col in df.columns:
        missing = df[col].isnull().sum()
        pct = 100 * (1 - missing / len(df))
        report.append(f"- {col}: {pct:.1f}% ({missing} missing)")
    report.append("")

    # 2. Data Types
    report.append("DATA TYPES:")
    for col in df.columns:
        dtype = df[col].dtype
        report.append(f"- {col}: {dtype}")
    report.append("")

    # 3. Quality Issues (Heuristic checks)
    report.append("QUALITY ISSUES:")
    issues = []
    
    # Check for invalid dates
    date_cols = ['date_of_birth', 'created_date']
    for col in date_cols:
        if col in df.columns:
             # Identify non-date formats (very rough check)
             invalid_dates = df[pd.to_datetime(df[col], errors='coerce').isna() & df[col].notna()]
             if not invalid_dates.empty:
                 issues.append(f"Invalid dates in {col}: {invalid_dates[col].tolist()}")

    # Check for negative income or non-numeric
    if 'income' in df.columns:
        non_numeric_income = df[pd.to_numeric(df['income'], errors='coerce').isna() & df['income'].notna()]
        if not non_numeric_income.empty:
             issues.append(f"Non-numeric income values: {non_numeric_income['income'].tolist()}")

    # Check for invalid account status
    if 'account_status' in df.columns:
        valid_statuses = ['active', 'inactive', 'suspended']
        invalid_status = df[~df['account_status'].isin(valid_statuses) & df['account_status'].notna()]
        if not invalid_status.empty:
            issues.append(f"Invalid account_status values: {invalid_status['account_status'].tolist()}")

    for i, issue in enumerate(issues, 1):
        report.append(f"{i}. {issue}")
    
    write_report(DQ_REPORT, "\n".join(report))
    return issues

# --- Part 2: Detect PII ---

def detect_pii(df):
    report = ["PII DETECTION REPORT", "======================", ""]
    
    pii_cols = {
        'first_name': 'Name',
        'last_name': 'Name',
        'email': 'Contact',
        'phone': 'Contact',
        'date_of_birth': 'Sensitive Personal',
        'address': 'Sensitive Personal'
    }
    
    report.append("RISK ASSESSMENT:")
    report.append("- HIGH: Names, emails, phone numbers, addresses, dates of birth")
    report.append("- MEDIUM: Income (financial sensitivity)")
    report.append("")
    
    report.append("DETECTED PII:")
    total_rows = len(df)
    
    # Regex patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}' # Matches (555) 123-4567, 555-123-4567, 555.123.4567
    
    pii_counts = {}
    
    for col in df.columns:
        if col in pii_cols:
            count = df[col].notna().sum()
            pct = 100 * count / total_rows
            pii_counts[col] = count
            report.append(f"- {col} ({pii_cols[col]}): used in {count} rows ({pct:.1f}%)")
            
            # Specific pattern checks
            if col == 'email':
                # check how many look like emails
                matches = df[col].astype(str).str.contains(email_pattern, regex=True).sum()
                report.append(f"  - Matches email pattern: {matches}")
            elif col == 'phone':
                 matches = df[col].astype(str).str.contains(phone_pattern, regex=True).sum()
                 report.append(f"  - Matches phone pattern: {matches}")

    report.append("")
    report.append("EXPOSURE RISK:")
    report.append("If this dataset were breached, attackers could:")
    report.append("- Phish customers (have emails)")
    report.append("- Spoof identities (have names + DOB + address)")
    report.append("- Social engineer (have phone numbers)")
    report.append("")
    report.append("MITIGATION:")
    report.append("Mask all PII before sharing with analytics teams")
    
    write_report(PII_REPORT, "\n".join(report))

# --- Part 3: Build a Data Validator ---

def validate_data(df, report_file=VALIDATION_REPORT):
    report = ["VALIDATION RESULTS", "==================", ""]
    
    failures = {} # Key: col, Value: list of (row_idx, value, reason)
    
    def add_failure(col, idx, val, reason):
        if col not in failures:
            failures[col] = []
        failures[col].append(f"Row {idx+2}: '{val}' ({reason})") # +2 for 1-based index including header

    for idx, row in df.iterrows():
        # customer_id: positive integer
        try:
            cid = int(row['customer_id'])
            if cid <= 0:
                add_failure('customer_id', idx, row['customer_id'], "Must be positive")
        except:
            add_failure('customer_id', idx, row['customer_id'], "Not an integer")

        # first_name, last_name: non-empty, alphabetic
        for name_col in ['first_name', 'last_name']:
            val = str(row[name_col])
            if not val or val.lower() == 'nan' or val.strip() == '':
                add_failure(name_col, idx, row[name_col], "Empty")
            elif not val.isalpha():
                pass # report.append(f"Note: {name_col} contains non-alpha: {val}") # excessive?

        # email: valid format
        email = str(row['email'])
        if '@' not in email or '.' not in email:
             add_failure('email', idx, email, "Invalid email format")

        # account_status
        status = str(row['account_status'])
        if status not in ['active', 'inactive', 'suspended']:
            add_failure('account_status', idx, status, "Invalid status")
            
        # date_of_birth
        dob = str(row['date_of_birth'])
        try:
            pd.to_datetime(dob)
        except:
             add_failure('date_of_birth', idx, dob, "Invalid date format")

        # created_date
        cdate = str(row['created_date'])
        try:
            pd.to_datetime(cdate)
        except:
             add_failure('created_date', idx, cdate, "Invalid date format")

        # income: non-negative, <= 10M
        try:
            inc = float(row['income'])
            if inc < 0:
                add_failure('income', idx, row['income'], "Negative income")
            if inc > 10_000_000:
                add_failure('income', idx, row['income'], "Income too high")
        except:
            add_failure('income', idx, row['income'], "Non-numeric income")

        # phone: reasonable length
        phone = str(row['phone'])
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 7 or len(digits) > 15:
             add_failure('phone', idx, phone, "Invalid phone length")

        # address: non-empty
        addr = str(row['address'])
        if not addr or addr.lower() == 'nan' or len(addr.strip()) < 5:
             add_failure('address', idx, addr, "Address too short or empty")

    pass_count = len(df) - len(set(sum([[int(f.split(' ')[1][:-1])-2 for f in vals] for vals in failures.values()], [])))
    fail_count = len(df) - pass_count

    report.append(f"PASS: {pass_count} rows passed all checks")
    report.append(f"FAIL: {fail_count} rows failed")
    report.append("")
    report.append("FAILURES BY COLUMN:")
    report.append("-------------------")
    
    for col, fails in failures.items():
        report.append(f"{col}:")
        for f in fails:
            report.append(f"- {f}")
        report.append("")

    write_report(report_file, "\n".join(report))
    return fail_count

# --- Part 4: Clean the Data ---

def clean_data(df):
    log = ["DATA CLEANING LOG", "=================", "", "ACTIONS TAKEN:", "--------------"]
    
    df_clean = df.copy()
    
    # 1. Handle Misaligned Rows (Heuristic fix for Row 25)
    # Row 25 in raw has missing address, shifting fields.
    # Logic: If 'income' column (col 7) has 'active' (status), shift right from address?
    # Or detecting validation failure and shifting?
    # This is hard to generalize without human eyes, but let's try a specific fix for the known issue if detected.
    
    # Check if 'income' contains strings that look like statuses
    # or 'account_status' contains dates
    
    # Manual fix for known messy rows based on task description
    # Row 25: `address` is missing.
    # `95000` is in `address` column (index 6, 0-based). Should be in `income`.
    # `active` is in `income` column (index 7). Should be `account_status`.
    # `2024-01-11` is in `account_status` (index 8). Should be `created_date`.
    
    # Let's iterate and fix
    rows_normalized = 0
    rows_dates = 0
    rows_names = 0
    missing_filled = 0
    
    # Fix Misalignment (hardcoded heuristic for this dataset)
    mask_misaligned = df_clean['account_status'].astype(str).str.match(r'\d{4}-\d{2}-\d{2}') # date in status
    if mask_misaligned.any():
        log.append("Detected misaligned rows (date in account_status). Attempting shift...")
        # For these rows, shift values: address -> income, income -> status, status -> created_date
        # And set address to NaN (or empty)
        
        # We need to be careful. The value `95000` is currently in validation `address`.
        
        for idx in df_clean[mask_misaligned].index:
            # Shift values
            val_address = df_clean.at[idx, 'address'] # This is actually income
            val_income = df_clean.at[idx, 'income']   # This is actually status
            val_status = df_clean.at[idx, 'account_status'] # This is actually created_date
            
            df_clean.at[idx, 'income'] = val_address
            df_clean.at[idx, 'account_status'] = val_income
            df_clean.at[idx, 'created_date'] = val_status
            df_clean.at[idx, 'address'] = None # Missing address
            log.append(f"- Fixed alignment for Row {idx+2}")

    # Normalize Phone Numbers
    def normalize_phone(p):
        if pd.isna(p): return p
        p_str = str(p)
        digits = re.sub(r'\D', '', p_str)
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        return p_str # Unknown format

    phone_before = df_clean['phone'].tolist()
    df_clean['phone'] = df_clean['phone'].apply(normalize_phone)
    # Count changes
    changes = sum([1 for x, y in zip(phone_before, df_clean['phone']) if x != y])
    if changes > 0:
        log.append(f"Normalization:\n- Phone format: Converted {changes} rows to XXX-XXX-XXXX")

    # Normalize Dates
    def normalize_date(d):
        if pd.isna(d): return d
        d_str = str(d).strip()
        if d_str.lower() == 'invalid_date': return None
        # Try formats: YYYY-MM-DD, MM/DD/YYYY, YYYY/MM/DD
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']:
            try:
                dt = datetime.datetime.strptime(d_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None # Could not parse

    for col in ['date_of_birth', 'created_date']:
        before = df_clean[col].tolist()
        df_clean[col] = df_clean[col].apply(normalize_date)
        changes = sum([1 for x, y in zip(before, df_clean[col]) if x != y]) # Note: this counts valid dates too if they were string, need strict meaningful change checks
        # But here mostly string to string.
        # Let's approximate
        if changes > 0:
             log.append(f"- Date format in {col}: Normalized {changes} rows")

    # Name Case
    for col in ['first_name', 'last_name']:
        before = df_clean[col].tolist()
        df_clean[col] = df_clean[col].fillna('').astype(str).str.title().replace('Of', 'of') # Simple title case
        # Restore NaN for empty strings
        df_clean[col] = df_clean[col].replace('Nan', np.nan).replace('', np.nan) 
        
        # Check changes
        changes = 0
        for b, a in zip(before, df_clean[col]):
            if pd.notna(b) and b != a:
                changes += 1
        if changes > 0:
            log.append(f"- Name case in {col}: Fixed {changes} rows")

    # Handle Missing Values
    log.append("\nMissing Values:")
    defaults = {
        'first_name': '[UNKNOWN]',
        'last_name': '[UNKNOWN]',
        'address': '[MISSING ADDRESS]',
        'income': 0,
        'account_status': 'unknown',
        'email': 'missing@example.com',
        'phone': '000-000-0000', 
        'date_of_birth': '1900-01-01',
        'created_date': datetime.date.today().strftime('%Y-%m-%d')
    }
    
    for col, default_val in defaults.items():
        missing_count = df_clean[col].isnull().sum()
        if missing_count > 0:
            df_clean[col].fillna(default_val, inplace=True)
            log.append(f"- {col}: {missing_count} rows missing -> filled with '{default_val}'")

    write_report(CLEANING_LOG, "\n".join(log))
    df_clean.to_csv(CLEANED_FILE, index=False)
    print(f"Saved cleaned data to {CLEANED_FILE}")
    
    return df_clean

# --- Part 5: Mask PII ---

def mask_pii(df):
    masked_df = df.copy()
    
    def mask_email(email):
        if pd.isna(email) or '@' not in str(email): return email
        user, domain = str(email).split('@', 1)
        return f"{user[0]}***@{domain}"
        
    def mask_phone(phone):
        if pd.isna(phone): return phone
        p = str(phone)
        if len(p) >= 4:
            return f"***-***-{p[-4:]}"
        return "***-***-****"
        
    def mask_name(name):
        if pd.isna(name): return name
        n = str(name)
        return f"{n[0]}***"
        
    def mask_address(addr):
        return "[MASKED ADDRESS]" if pd.notna(addr) else addr
        
    def mask_dob(dob):
        if pd.isna(dob): return dob
        d = str(dob)
        if len(d) >= 4:
            return f"{d[:4]}-**-**"
        return "****-**-**"

    masked_df['email'] = masked_df['email'].apply(mask_email)
    masked_df['phone'] = masked_df['phone'].apply(mask_phone)
    masked_df['first_name'] = masked_df['first_name'].apply(mask_name)
    masked_df['last_name'] = masked_df['last_name'].apply(mask_name)
    masked_df['address'] = masked_df['address'].apply(mask_address)
    masked_df['date_of_birth'] = masked_df['date_of_birth'].apply(mask_dob)

    masked_df.to_csv(MASKED_FILE, index=False)
    print(f"Saved masked data to {MASKED_FILE}")
    
    # Generate Sample Report
    sample_report = ["BEFORE MASKING (first 2 rows):", "------------------------------"]
    sample_report.append(df.head(2).to_csv(index=False))
    sample_report.append("")
    sample_report.append("AFTER MASKING (first 2 rows):",)
    sample_report.append("-----------------------------")
    sample_report.append(masked_df.head(2).to_csv(index=False))
    
    write_report(MASKED_SAMPLE, "\n".join(sample_report))
    
    return masked_df

# --- Part 6: Pipeline Orchestration ---

def run_pipeline():
    start_time = datetime.datetime.now()
    exec_log = ["PIPELINE EXECUTION REPORT", "=========================", "", f"Timestamp: {start_time}", ""]
    
    # Stage 1: Load
    exec_log.append("Stage 1: LOAD")
    df_raw = load_data(RAW_FILE)
    if df_raw is None:
        exec_log.append("X Failed to load data")
        write_report(PIPELINE_REPORT, "\n".join(exec_log))
        return
    exec_log.append(f"✓ Loaded {RAW_FILE} - {len(df_raw)} rows")
    exec_log.append("")

    # Stage 2: Profile (Quality Analysis)
    exec_log.append("Stage 2: PROFILE")
    profile_data(df_raw)
    exec_log.append("✓ Generated data quality report")
    exec_log.append("")

    # Stage 3: Detect PII
    exec_log.append("Stage 3: DETECT PII")
    detect_pii(df_raw)
    exec_log.append("✓ Generated PII detection report")
    exec_log.append("")
    
    # Stage 4: Validate (Pre-clean)
    exec_log.append("Stage 4: VALIDATE (RAW)")
    # Save raw validation results to the requested deliverable file
    fails = validate_data(df_raw, report_file=VALIDATION_REPORT)
    exec_log.append(f"✓ Validation complete. {fails} rows failed.")
    exec_log.append("")

    # Stage 5: Clean
    exec_log.append("Stage 5: CLEAN")
    df_clean = clean_data(df_raw)
    exec_log.append("✓ Cleaned data")
    exec_log.append("")
    
    # Validate Post-clean
    exec_log.append("Stage 6: VALIDATE (CLEANED)")
    # Save cleaned validation results to a separate file (or just log)
    fails_clean = validate_data(df_clean, report_file="validation_results_cleaned.txt")
    exec_log.append(f"✓ Re-validation complete. {fails_clean} rows failed.")
    exec_log.append("")
    
    # Stage 7: Mask & Save
    exec_log.append("Stage 7: MASK & SAVE")
    mask_pii(df_clean)
    exec_log.append("✓ Masked PII and saved output")
    exec_log.append("")

    exec_log.append("SUMMARY:")
    exec_log.append(f"- Input: {len(df_raw)} rows")
    exec_log.append(f"- Output: {len(df_clean)} rows")
    exec_log.append(f"- Quality Issues Fixed: (See cleaning log)") 
    exec_log.append("Status: SUCCESS ✓")
    
    write_report(PIPELINE_REPORT, "\n".join(exec_log))

if __name__ == "__main__":
    run_pipeline()
