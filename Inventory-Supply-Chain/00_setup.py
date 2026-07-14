# Databricks notebook source
# DBTITLE 1,Cell 1
# Storage details
storage_account = "iaspstorage3"
container = "iaspcontainer"
access_key = "<YOUR_ACCESS_KEY_HERE>"

# Configure Spark to access ADLS Gen2
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    access_key
)

print("ADLS connection configured successfully!")

# COMMAND ----------

# DBTITLE 1,Cell 2
display(
        dbutils.fs.ls(
                f"abfss://{container}@{storage_account}.dfs.core.windows.net/"
                    )
                    )

# COMMAND ----------

spark.conf.get(f"fs.azure.account.key.iaspstorage3.dfs.core.windows.net")

# COMMAND ----------

products_df = spark.read \
        .option("header", "true") \
            .csv(
                    f"abfss://{container}@{storage_account}.dfs.core.windows.net/raw/products.csv"
                        )

display(products_df)
                        