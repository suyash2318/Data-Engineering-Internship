# Week 7: Incremental Data Processing using Delta Lake (Superstore Dataset)

This assignment demonstrates how to implement an incremental data ingestion pipeline (SCD Type 1) using PySpark and Delta Lake, processing the Kaggle Superstore sales dataset.

---

## Steps Executed

1. **Spark & Delta Lake Setup**: Configured the PySpark SparkSession extensions to support the Delta catalog and execution engines.
2. **Dataset Download**: Used `kagglehub` to programmatically fetch the `vivek468/superstore-dataset-final` containing `Sample - Superstore.csv`.
3. **Data Cleaning**:
   - Cleaned column headers to lower snake_case.
   - Removed duplicates on `row_id` and handled missing customer records.
4. **Delta Table Conversion**: Saved the cleaned base Superstore dataset as a Delta table.
5. **Incremental Load**: Created a secondary dataframe representing incremental transactions (updates to existing sales/profit and new entries).
6. **Delta Merge Operation**: Executed a `MERGE` operation (matching on `row_id` keys) to:
   - Update matching records with modified sales/profit metrics.
   - Insert new records if they do not match.
7. **Validation**: Verified that the row counts are correct and that the primary key (`row_id`) remains unique.

---

## Output Files
- **Jupyter Notebook**: [notebooks/delta_scd_assignment.ipynb](file:///d:/My%20Projects/CelabalWeek8/Week-07_Delta_Lake_Assignment/notebooks/delta_scd_assignment.ipynb)
- **Data Folder**: [data/](file:///d:/My%20Projects/CelabalWeek8/Week-07_Delta_Lake_Assignment/data/)
- **Screenshots Directory**: [screenshots/](file:///d:/My%20Projects/CelabalWeek8/Week-07_Delta_Lake_Assignment/screenshots/)

---

## Verification & Validations
- Total row count is validated to increase by the exact count of new inserts (Original Count + 1).
- Validated that `row_id` keys are completely unique (`assert final_count == unique_count`).
- Verified updates:
  - Row ID `1` was successfully updated to sales `350.00` and profit `50.00`.
  - Row ID `2` was successfully updated to sales `800.00` and profit `120.00`.
  - Row ID `99999` was successfully appended.
