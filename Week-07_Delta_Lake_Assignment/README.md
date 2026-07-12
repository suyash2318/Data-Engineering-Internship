# Week 7: Incremental Data Processing using Delta Lake

This assignment demonstrates how to implement an incremental data ingestion pipeline (SCD Type 1) using PySpark and Delta Lake. 

Incremental data loading ensures that changed records are updated in place and new records are appended, maintaining a single clean, deduplicated version of the master table without rewriting the entire dataset.

---

## Steps Executed

1. **Spark & Delta Lake Setup**: Configured the PySpark SparkSession extensions to support the Delta catalog and execution engines.
2. **Initial Ingestion**: Loaded `customer_master.csv` containing raw historical customer records.
3. **Data Cleaning**:
   - Replaced missing values (`email` nulls) with a placeholder.
   - Removed duplicates on `customer_id` using Pandas/PySpark dataframe cleaning operations.
4. **Delta Table Conversion**: Saved the cleaned base master dataset as a Delta table.
5. **Incremental Load**: Read `customer_incremental.csv` containing both new customers and modifications to existing ones.
6. **Delta Merge Operation**: Executed a `MERGE` operation (matching on `customer_id` keys) to:
   - Update matching records with updated email, name, and city.
   - Insert new records if they do not match.
7. **Validation**: Verified that the row counts are consistent and that the `customer_id` keys remain unique.

---

## Output Files
- **Data Directory**: [data/](file:///d:/My%20Projects/CelabalWeek8/Week-07_Delta_Lake_Assignment/data/)
  - `customer_master.csv`: Base customer database.
  - `customer_incremental.csv`: Incremental update records.
- **Jupyter Notebook**: [notebooks/delta_scd_assignment.ipynb](file:///d:/My%20Projects/CelabalWeek8/Week-07_Delta_Lake_Assignment/notebooks/delta_scd_assignment.ipynb)

---

## Verification & Validations
- Total row count of final table is `5` rows.
- Validated that `customer_id` keys are completely unique (`assert total_rows == unique_ids`).
- Verified updates:
  - Customer `102` (`Jane Smith`) was updated to email `jane_new@example.com` and city `San Francisco`.
  - Customer `104` (`Alice Brown`) was updated with email `alice@example.com`.
  - Customer `106` (`Charlie Green`) was inserted.
