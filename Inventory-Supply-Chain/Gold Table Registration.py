# Databricks notebook source
spark.sql(f"""
CREATE DATABASE IF NOT EXISTS inventory_db
""")

# COMMAND ----------

# DBTITLE 1,Cell 2
spark.conf.set(
    "fs.azure.account.key.iaspstorage3.dfs.core.windows.net",
    "<YOUR_ACCESS_KEY_HERE>"
)

gold_tables = [
    "inventory_snapshot",
    "low_stock_alert",
    "supplier_performance",
    "sales_summary",
    "sales_trend"
]
GOLD_DIR = "abfss://iaspcontainer@iaspstorage3.dfs.core.windows.net/gold"

for table in gold_tables:
    (
        spark.read.format("delta").load(f"{GOLD_DIR}/{table}")
        .write.format("delta")
        .mode("overwrite")
        .saveAsTable(f"inventory_db.{table}")
    )
    print(f"Registered inventory_db.{table}")

print("All Gold tables registered.")



# COMMAND ----------

spark.sql("SHOW TABLES IN inventory_db").show()