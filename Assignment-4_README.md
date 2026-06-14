# Azure Cloud Fundamentals and Data Pipeline Implementation using ADF

## Objective
To understand Azure cloud concepts and build an end-to-end data pipeline using Azure Storage Account and Azure Data Factory.

## Dataset
Sample - Superstore.csv

## Azure Services Used
- Azure Resource Group
- Azure Storage Account
- Azure Blob Storage
- Azure Data Factory (ADF)

## Steps Performed
1. Created a Resource Group.
2. Created an Azure Storage Account.
3. Created Blob Containers:
   - input-data
   - output-data
4. Uploaded Sample-Superstore.csv to the input container.
5. Created an Azure Data Factory instance.
6. Configured Blob Storage Linked Service.
7. Created Source and Destination CSV Datasets.
8. Added Get Metadata activity to validate source file information.
9. Added Copy Data activity to copy data from input-data to output-data.
10. Executed the pipeline using Debug/Trigger.
11. Monitored execution and verified successful completion.
12. Verified the copied file in the output container.
13. Configured required IAM role assignments.

## Pipeline Flow
Input Blob Container → Get Metadata → Copy Data → Output Blob Container

## Result
The pipeline executed successfully. Metadata validation and file copy operations completed without errors, and the destination file was successfully created in the output container.

## Screenshots Included
- Resource Group Overview
- Storage Account
- Input Container
- Azure Data Factory Home
- Linked Service
- Source Dataset
- Destination Dataset
- Get Metadata Activity
- Copy Data Activity
- Pipeline Success
- Monitor Runs
- Output Container
- IAM Role Assignment

## Conclusion
Successfully implemented an end-to-end Azure Data Factory pipeline using Azure Blob Storage as source and destination, including metadata validation, data movement, monitoring, and access management.
