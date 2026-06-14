# SuyashMaheshwari_JECRC(College)_Week1_python-data-cleaning

This project demonstrates basic data exploration and cleaning using Python Pandas.

## Tasks Performed
- Loaded CSV dataset
- Explored dataset
- Handled missing values
- Filtered rows and selected columns
- Removed duplicates
- Created derived column
- Saved cleaned dataset

## Tools Used
- Python
- Pandas
- Jupyter Notebook


# SuyashMaheshwari_JECRC(College)_Week2_SQL_Data_Analysis

This project demonstrates SQL-based data analysis using Python, Pandas, SQLite, and Jupyter Notebook on the Superstore sales dataset.

## Tasks Performed

* Loaded compressed CSV dataset
* Explored dataset structure and columns
* Converted dataset into SQL table using SQLite
* Performed filtering using WHERE clause
* Applied aggregation using GROUP BY
* Calculated sales, profit, quantity, and averages
* Identified top products and top customers
* Analyzed monthly sales trends
* Checked duplicate and null records
* Performed business insights analysis
* Exported results through Jupyter Notebook

## SQL Concepts Used

* SELECT
* WHERE
* GROUP BY
* ORDER BY
* HAVING
* LIMIT
* Aggregate Functions

  * SUM()
  * AVG()
  * COUNT()
  * MAX()
  * MIN()
* DISTINCT
* Data Validation Queries

## Tools Used

* Python
* Pandas
* SQLite
* Jupyter Notebook

## Dataset Used

* Superstore Sales Dataset (.csv.gz)

	# SuyashMaheshwari_JECRC(College)_Week-3_SQL(Subqueries)

What I used and when:

Subqueries — filtering rows against an aggregated value (like avg or max). Works well for simple comparisons
CTEs — breaking down complex queries into readable named blocks. Way easier to debug than deeply nested subqueries
Window Functions — RANK(), ROW_NUMBER(), DENSE_RANK() for ordering and numbering without collapsing the result set the way GROUP BY does
Key findings:

Sean Miller is the #1 customer at 17.5k order
Jeffrey Brumfield is at the very bottom with just $3.52 total
Only 294 out of 793 customers (about 37%) are above the average total sales of ~$2297
12 customers placed just a single order — most of these overlap with the lowest spenders
The data is heavily right-skewed with a small number of high-value customers pulling the average up

## Project Outcome

The project successfully demonstrated how SQL queries can be used for business-oriented sales analysis, customer insights, product performance evaluation, and data quality validation using a real-world dataset.

	# SuyashMaheshwari_JECRC(College)_Week-4_AZURE
 Azure Cloud Fundamentals and Data Pipeline Implementation using ADF
Objective
To understand Azure cloud concepts and build an end-to-end data pipeline using Azure Storage Account and Azure Data Factory.

Dataset
Sample - Superstore.csv

Azure Services Used
Azure Resource Group
Azure Storage Account
Azure Blob Storage
Azure Data Factory (ADF)
Steps Performed
Created a Resource Group.
Created an Azure Storage Account.
Created Blob Containers:
input-data
output-data
Uploaded Sample-Superstore.csv to the input container.
Created an Azure Data Factory instance.
Configured Blob Storage Linked Service.
Created Source and Destination CSV Datasets.
Added Get Metadata activity to validate source file information.
Added Copy Data activity to copy data from input-data to output-data.
Executed the pipeline using Debug/Trigger.
Monitored execution and verified successful completion.
Verified the copied file in the output container.
Configured required IAM role assignments.
Pipeline Flow
Input Blob Container → Get Metadata → Copy Data → Output Blob Container

Result
The pipeline executed successfully. Metadata validation and file copy operations completed without errors, and the destination file was successfully created in the output container.

Screenshots Included
Resource Group Overview
Storage Account
Input Container
Azure Data Factory Home
Linked Service
Source Dataset
Destination Dataset
Get Metadata Activity
Copy Data Activity
Pipeline Success
Monitor Runs
Output Container
IAM Role Assignment
Conclusion
Successfully implemented an end-to-end Azure Data Factory pipeline using Azure Blob Storage as source and destination, including metadata validation, data movement, monitoring, and access management.
 
