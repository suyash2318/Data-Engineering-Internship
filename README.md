# Celabal Technologies - Data Engineering Internship

A comprehensive repository containing all my project assignments and data pipelines developed during my Data Engineering Internship at Celabal Technologies.

## 📁 Repository Directory

This repository is structured sequentially to showcase learning milestones and progress:

| Week / Assignment | Topic | Description | Technologies |
| :--- | :--- | :--- | :--- |
| **[Week 1](./Week-01_Python_Data_Cleaning)** | Python Data Cleaning | Raw data parsing, filtering, handling duplicates/missing entries | `Python`, `Pandas`, `Jupyter Notebook` |
| **[Week 2](./Week-02_SQL_Data_Analysis)** | SQL Data Analysis | Loading datasets into SQLite and performing analytical queries | `SQL`, `SQLite`, `Pandas` |
| **[Week 3](./Week-03_SQL_Subqueries)** | SQL Subqueries & Joins | Utilizing CTEs, window functions, and subqueries for sales analysis | `SQL`, `CTEs`, `Window Functions` |
| **[Week 4](./Week-04_Azure_Data_Factory)** | Azure ADF Pipelines | Building end-to-end blob storage copy pipelines with metadata validation | `Azure Blob Storage`, `Data Factory`, `IAM` |
| **[Week 5](./Week-05_Spark_Introduction)** | Spark Dataframes | Loading and analyzing datasets with Apache Spark DataFrames | `Apache Spark`, `PySpark` |
| **[Week 6](./Week-06_PySpark_DataFrame)** | Advanced PySpark | Executing PySpark operations on larger datasets and optimizing execution | `Apache Spark`, `PySpark` |
| **[Week 7](./Week-07_Delta_Lake_Assignment)** | Delta Lake Ingestion | Incremental data updates (SCD Type 1) using Spark and Delta tables | `PySpark`, `Delta Lake`, `SCD` |
| **[Week 8](./Week-08_Ecommerce_Analytics)** | E-Commerce Analytics System | Refactored transaction data pipeline with robust cleaning and CLI | `Python`, `SQLite`, `Pandas`, `CLI` |

---

## 🛠️ Assignment Summaries

### Week 1: Python Data Cleaning
*Demonstrates basic data exploration and cleaning using Pandas.*
- Loaded CSV datasets and handled missing values.
- Removed duplicates and performed column selection.
- Created derived fields and exported clean files.

### Week 2: SQL Data Analysis
*Demonstrates SQL-based data analysis on the Superstore sales dataset.*
- Converted CSVs into local relational SQL tables.
- Applied aggregate functions (`SUM`, `AVG`, `COUNT`) and filters (`WHERE`, `HAVING`).
- Identified top-performing products and customer demographics.

### Week 3: SQL Subqueries & Joins
*In-depth utilization of CTEs and analytical window functions.*
- Applied subqueries to filter rows against aggregated averages.
- Used CTEs to break down complex queries into readable, debuggable named blocks.
- Calculated rank and row numbers using Window Functions.

### Week 4: Azure Cloud Fundamentals & ADF Pipelines
*Design and implementation of cloud-based data movement.*
- Configured Resource Groups, Storage Accounts, and Blob Storage Containers.
- Set up an Azure Data Factory (ADF) instance.
- Built a data movement pipeline: `Get Metadata` -> validation -> `Copy Data` activity.

### Week 5 & 6: Apache Spark & PySpark
*Processing data at scale with Apache Spark.*
- Built PySpark scripts to clean and transform datasets.
- Handled schema definition and dataframe optimization.

### Week 7: Delta Lake Ingestion
*Incremental data updates (SCD Type 1) using Spark and Delta tables.*
- Configured Spark session for Delta extensions and catalogs.
- Performed deduplication, NULL resolution, and loaded clean customer profiles.
- Applied Delta `MERGE` statements to perform updates and insertions.

### Week 8: E-Commerce Analytics System
*A complete end-to-end data pipeline built with Python and SQL.*
- **Data Generation**: Generates transactional datasets with intentional quality anomalies.
- **Data Cleaning**: Python pipeline normalizing email formats, correcting dates, and capping bounds.
- **SQL Analysis**: 16 analytical queries (aggregations, cohort retention, YoY growth, and self-joins).
- **CLI Tool**: Stdlib-only reporting tool generating daily, weekly, and monthly summaries with periodic comparisons.
