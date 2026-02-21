# Customer Data Pipeline and PII Masking

## Overview
This repository contains an enterprise-grade ETL (Extract, Transform, Load) pipeline designed to ingest raw customer records, enforce strict data quality rules, and mask Personally Identifiable Information (PII) to ensure privacy and compliance before data reaches downstream analytics environments.

## Architecture
The pipeline has been engineered with a modular architecture, isolating concerns into dedicated source packages. Validation is handled using Pydantic to ensure strict schema adherence.

## Project Structure
```
PII/
├── main.py                     # Pipeline orchestrator
├── customers_raw.csv           # Input raw dataset
├── requirements.txt            # Project dependencies
├── src/
│   ├── profiling/              # Completeness and data type analysis
│   ├── pii/                    # Regex-based PII detection and risk scoring
│   ├── validation/             # Pydantic schema validation models
│   ├── cleaning/               # Data normalization and row-alignment fixes
│   └── masking/                # PII redaction and formatting
├── data/                       # Generated output artifacts
│   ├── customers_cleaned.csv
│   └── customers_masked.csv
├── reports/                    # Generated audit and execution logs
│   ├── pipeline_execution_report.txt
│   ├── data_quality_report.txt
│   ├── pii_detection_report.txt
│   ├── validation_results.txt
│   └── cleaning_log.txt
└── docs/
    └── reflection.md           # Governance and architectural reflection
```

## Pipeline Stages

The orchestrator (`main.py`) executes the following stages in sequence:
 
1. **Load:** Ingests the raw CSV file.
2. **Profile:** Analyzes the raw data for completeness, data type mismatches, and structural anomalies.
3. **Detect PII:** Scans categorical fields to identify sensitive data (Names, Emails, Phones, Dates of Birth) and assigns a risk level.
4. **Validate (Raw):** Attempts to parse the raw data through the Pydantic schema, logging constraint violations.
5. **Clean:** Normalizes temporal data, standardizes phone formats, handles null values, and dynamically realigns misaligned rows.
6. **Validate (Cleaned):** Re-validates the transformed data to ensure it meets the target schema.
7. **Mask & Save:** Redacts sensitive information while preserving analytical utility, generating the final output datasets.

## Requirements and Installation

The project requires Python 3.10 or higher. 

To install the required dependencies:
```bash
pip install pandas pydantic[email]
```

## Execution

To execute the entire pipeline, run the root orchestrator script:
```bash
python main.py
```

Upon successful execution, the terminal will log the pipeline stages, and the `data/` and `reports/` directories will be populated with the latest artifacts.

## Configuration and Logging
The pipeline utilizes standard Python logging configured at the `INFO` level to provide real-time visibility into the execution lifecycle. Detailed row-level anomalies (such as Pydantic ValidationErrors) are routed directly into text-based report files within the `reports/` directory to prevent console fatigue.
