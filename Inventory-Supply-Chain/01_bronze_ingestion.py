# Databricks notebook source
from pyspark.sql.functions import *
from pyspark.sql.types import *

# COMMAND ----------

storage_account = "iaspstorage3"
container = "iaspcontainer"

base_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net"

raw_path = f"{base_path}/raw"
bronze_path = f"{base_path}/bronze"
checkpoint_path = f"{base_path}/checkpoints"
schema_path = f"{base_path}/schema"

print(base_path)

# COMMAND ----------

# DBTITLE 1,Cell 3
def ingest_table(table_name):

    stream_df = (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "csv")
            .option("header", "true")
            .option("cloudFiles.inferColumnTypes", "true")
            .option(
                "cloudFiles.schemaLocation",
                f"{schema_path}/{table_name}"
            )
            .load(f"{raw_path}/{table_name}")
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("source_file_name", col("_metadata.file_path"))
    )

    (
        stream_df.writeStream
            .format("delta")
            .option(
                "checkpointLocation",
                f"{checkpoint_path}/{table_name}"
            )
            .trigger(availableNow=True)
            .start(f"{bronze_path}/{table_name}")
            .awaitTermination()
    )

    print(f"{table_name} Bronze table created.")

# COMMAND ----------

spark.conf.set(
        f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
            '<YOUR_ACCESS_KEY_HERE>'
            )


# COMMAND ----------

# DBTITLE 1,Cell 5
spark.read.format("delta").load(f"{bronze_path}/products")

# COMMAND ----------

display(dbutils.fs.ls(f"{raw_path}/products"))

# COMMAND ----------

dbutils.fs.rm(f"{schema_path}/products", True)
dbutils.fs.rm(f"{checkpoint_path}/products", True)
dbutils.fs.rm(f"{bronze_path}/products", True)

# COMMAND ----------

ingest_table("products")

# COMMAND ----------

tables = [

    "products",
    "inventory",
    "suppliers",
    "warehouses",
    "transactions",
    "shipments"
]
for table in tables:
    ingest_table(table)

# COMMAND ----------

display(spark.read.format("delta").load(f"{bronze_path}/transactions"))