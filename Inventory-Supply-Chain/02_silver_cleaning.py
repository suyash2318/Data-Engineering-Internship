# Databricks notebook source
# DBTITLE 1,Cell 1
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, when, upper, trim, row_number, to_date, to_timestamp,
    lit, current_date, date_sub, expr
)
from delta.tables import DeltaTable
# Databricks notebook source
storage_account = "iaspstorage3"
container = "iaspcontainer"

BASE_PATH = f"abfss://{container}@{storage_account}.dfs.core.windows.net"
RAW_DIR = f"{BASE_PATH}/raw"
BRONZE_DIR = f"{BASE_PATH}/bronze"
SILVER_DIR = f"{BASE_PATH}/silver"
GOLD_DIR = f"{BASE_PATH}/gold"
CHECKPOINT_DIR = f"{BASE_PATH}/checkpoints"
SCHEMA_DIR = f"{BASE_PATH}/schema"

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def deduplicate(df, partition_col, order_cols):
    """Keep only the latest row per partition key using row_number window."""
    window_spec = Window.partitionBy(partition_col).orderBy(
        *[col(c).desc() for c in order_cols]
    )
    return (
        df.withColumn("_row_num", row_number().over(window_spec))
        .filter(col("_row_num") == 1)
        .drop("_row_num")
    )


def clean_warehouses(spark):
    bronze_path = f"{BRONZE_DIR}/warehouses"
    silver_path = f"{SILVER_DIR}/warehouses"

    df = spark.read.format("delta").load(bronze_path)
    df = df.filter(col("warehouse_id").isNotNull())

    df = df.withColumn("capacity", col("capacity").cast("integer")) \
           .filter(col("capacity") > 0)

    # Standardize text fields
    for field in ["warehouse_name", "location_city", "location_state",
                  "country", "warehouse_type", "manager_name", "operational_status"]:
        df = df.withColumn(field, upper(trim(col(field))))

    df = df.withColumn("created_date", to_date(col("created_date")))

    df = deduplicate(df, "warehouse_id", ["created_date", "ingestion_timestamp"])
    df = df.drop("ingestion_timestamp", "source_file_name")

    df.write.format("delta").mode("overwrite").save(silver_path)
    print(f"Cleaned silver_warehouses table saved. Rows: {df.count()}")


def clean_suppliers(spark):
    bronze_path = f"{BRONZE_DIR}/suppliers"
    silver_path = f"{SILVER_DIR}/suppliers"

    df = spark.read.format("delta").load(bronze_path)
    df = df.filter(col("supplier_id").isNotNull())

    # Cast types
    df = df.withColumn("rating", col("rating").cast("integer")) \
           .withColumn("lead_time_days", col("lead_time_days").cast("integer")) \
           .withColumn("contract_start_date", to_date(col("contract_start_date"))) \
           .withColumn("contract_end_date", to_date(col("contract_end_date"))) \
           .withColumn("is_active", col("is_active").cast("boolean"))

    # Validate: rating 1-5, valid email, contract dates make sense
    df = df.filter(
        (col("rating") >= 1) & (col("rating") <= 5) &
        col("contact_email").rlike(EMAIL_REGEX) &
        ((col("contract_end_date").isNull()) | (col("contract_start_date") < col("contract_end_date")))
    )

    for field in ["supplier_name", "country", "region", "contact_name", "contact_email"]:
        df = df.withColumn(field, upper(trim(col(field))))

    df = deduplicate(df, "supplier_id", ["contract_start_date", "ingestion_timestamp"])
    df = df.drop("ingestion_timestamp", "source_file_name")

    df.write.format("delta").mode("overwrite").save(silver_path)
    print(f"Cleaned silver_suppliers table saved. Rows: {df.count()}")


def clean_inventory(spark):
    bronze_path = f"{BRONZE_DIR}/inventory"
    silver_path = f"{SILVER_DIR}/inventory"

    df = spark.read.format("delta").load(bronze_path)
    df = df.filter(col("inventory_id").isNotNull())

    df = df.withColumn("stock_quantity", col("stock_quantity").cast("integer")) \
           .withColumn("reserved_quantity", col("reserved_quantity").cast("integer")) \
           .withColumn("damaged_quantity", col("damaged_quantity").cast("integer")) \
           .withColumn("last_restock_date", to_date(col("last_restock_date"))) \
           .withColumn("last_updated", to_date(col("last_updated"))) \
           .filter(col("stock_quantity") >= 0)

    df = df.na.fill({"reserved_quantity": 0, "damaged_quantity": 0})

    # Derived column: what's actually available to sell
    df = df.withColumn(
        "available_stock",
        col("stock_quantity") - col("reserved_quantity") - col("damaged_quantity")
    )

    for field in ["product_id", "warehouse_id", "batch_id"]:
        df = df.withColumn(field, upper(trim(col(field))))

    df = deduplicate(df, "inventory_id", ["last_updated", "ingestion_timestamp"])
    df = df.drop("ingestion_timestamp", "source_file_name")

    df.write.format("delta").mode("overwrite").save(silver_path)
    print(f"Cleaned silver_inventory table saved. Rows: {df.count()}")


def clean_transactions(spark):
    bronze_path = f"{BRONZE_DIR}/transactions"
    silver_path = f"{SILVER_DIR}/transactions"

    df = spark.read.format("delta").load(bronze_path)
    df = df.filter(col("transaction_id").isNotNull())

    df = df.withColumn("quantity", col("quantity").cast("integer")) \
           .withColumn("unit_price", col("unit_price").cast("float")) \
           .withColumn("transaction_timestamp", to_timestamp(col("transaction_timestamp"))) \
           .filter((col("quantity") > 0) & (col("unit_price") >= 0))

    # Recalculate total_price from source values
    df = df.withColumn("total_price", col("quantity") * col("unit_price"))

    for field in ["transaction_type", "product_id", "warehouse_id",
                  "supplier_id", "channel", "reference_id"]:
        df = df.withColumn(field, upper(trim(col(field))))

    # Only keep valid transaction types
    df = df.filter(col("transaction_type").isin("IN", "OUT", "TRANSFER", "RETURN"))

    df = deduplicate(df, "transaction_id", ["transaction_timestamp", "ingestion_timestamp"])
    df = df.drop("ingestion_timestamp", "source_file_name")

    df.write.format("delta").mode("overwrite").save(silver_path)
    print(f"Cleaned silver_transactions table saved. Rows: {df.count()}")


def clean_shipments(spark):
    bronze_path = f"{BRONZE_DIR}/shipments"
    silver_path = f"{SILVER_DIR}/shipments"

    df = spark.read.format("delta").load(bronze_path)
    df = df.filter(col("shipment_id").isNotNull())

    df = df.withColumn("shipment_date", to_date(col("shipment_date"))) \
           .withColumn("delivery_date", to_date(col("delivery_date"))) \
           .withColumn("shipping_cost", col("shipping_cost").cast("float"))

    # delivery can't be before shipment
    df = df.filter(
        (col("delivery_date").isNull()) | (col("delivery_date") >= col("shipment_date"))
    )

    # Calculate delay; keep existing value if delivery_date is missing
    df = df.withColumn(
        "delay_days",
        when(col("delivery_date").isNotNull(), expr("datediff(delivery_date, shipment_date)"))
        .otherwise(col("delay_days").cast("integer"))
    )

    for field in ["shipment_status", "supplier_id", "warehouse_id"]:
        df = df.withColumn(field, upper(trim(col(field))))

    df = deduplicate(df, "shipment_id", ["shipment_date", "ingestion_timestamp"])
    df = df.drop("ingestion_timestamp", "source_file_name")

    df.write.format("delta").mode("overwrite").save(silver_path)
    print(f"Cleaned silver_shipments table saved. Rows: {df.count()}")


def clean_products_scd2(spark):
    """Handle products with SCD Type 2 — track historical changes by expiring old rows."""
    bronze_path = f"{BRONZE_DIR}/products"
    silver_path = f"{SILVER_DIR}/products"

    df = spark.read.format("delta").load(bronze_path)
    df = df.filter(col("product_id").isNotNull())

    # Cast and clean
    df = df.withColumn("cost_price", col("cost_price").cast("float")) \
           .withColumn("selling_price", col("selling_price").cast("float")) \
           .withColumn("weight", col("weight").cast("float")) \
           .withColumn("reorder_level", col("reorder_level").cast("integer")) \
           .withColumn("launch_date", to_date(col("launch_date"))) \
           .withColumn("expiry_date", to_date(col("expiry_date"))) \
           .withColumn("last_updated", to_date(col("last_updated")))

    for field in ["product_name", "category", "brand", "currency",
                  "supplier_id", "product_status", "dimensions"]:
        df = df.withColumn(field, upper(trim(col(field))))

    # Keep only the latest version per product in this batch
    df = deduplicate(df, "product_id", ["last_updated", "ingestion_timestamp"])
    df = df.drop("ingestion_timestamp", "source_file_name")

    # First run: just write the initial table with SCD2 columns
    if not DeltaTable.isDeltaTable(spark, silver_path):
        df_initial = (
            df.withColumn("start_date", current_date())
              .withColumn("end_date", lit(None).cast("date"))
              .withColumn("current_flag", lit("Y"))
        )

        df_initial.write \
            .format("delta") \
            .mode("overwrite") \
            .save(silver_path)

        print(f"Initialized silver_products table. Rows: {df_initial.count()}")
        return

    # Subsequent runs: merge with SCD2 logic
    silver_table = DeltaTable.forPath(spark, silver_path)
    df_silver_active = silver_table.toDF().filter(col("current_flag") == "Y")

    # Find products that changed (exist in both but values differ)
    tracked_fields = ["product_name", "category", "brand", "cost_price",
                      "selling_price", "reorder_level", "product_status"]

    change_condition = None
    for field in tracked_fields:
        cond = col(f"src.{field}") != col(f"tgt.{field}")
        change_condition = cond if change_condition is None else (change_condition | cond)

    df_changed = df.alias("src").join(
        df_silver_active.alias("tgt"), "product_id"
    ).filter(change_condition)

    # Find completely new products (not in silver at all)
    df_new = df.alias("src").join(
        df_silver_active.alias("tgt"), "product_id", "left_outer"
    ).filter(col("tgt.product_id").isNull()).select("src.*")

    # SCD2 merge trick: use a merge_key column
    # - For records to expire: merge_key = product_id (matches existing row)
    # - For records to insert: merge_key = null (forces insert, no match)
    df_to_expire = df_changed.select("src.*").withColumn("merge_key", col("product_id"))
    df_to_insert = df_changed.select("src.*").union(df_new).withColumn("merge_key", lit(None).cast("string"))

    df_merge_source = df_to_expire.union(df_to_insert)

    (
        silver_table.alias("tgt")
        .merge(
            df_merge_source.alias("src"),
            "tgt.product_id = src.merge_key AND tgt.current_flag = 'Y'"
        )
        .whenMatchedUpdate(set={
            "end_date": date_sub(current_date(), 1),
            "current_flag": lit("N")
        })
        .whenNotMatchedInsert(values={
            "product_id": "src.product_id",
            "product_name": "src.product_name",
            "category": "src.category",
            "brand": "src.brand",
            "cost_price": "src.cost_price",
            "selling_price": "src.selling_price",
            "currency": "src.currency",
            "supplier_id": "src.supplier_id",
            "product_status": "src.product_status",
            "launch_date": "src.launch_date",
            "expiry_date": "src.expiry_date",
            "weight": "src.weight",
            "dimensions": "src.dimensions",
            "reorder_level": "src.reorder_level",
            "last_updated": "src.last_updated",
            "start_date": current_date(),
            "end_date": lit(None).cast("date"),
            "current_flag": lit("Y")
        })
        .execute()
    )
    print("SCD Type 2 Products Merge Completed.")


def run_silver_cleaning(spark):
    """Clean all Bronze tables and write to Silver."""


    clean_warehouses(spark)
    clean_suppliers(spark)
    clean_inventory(spark)
    clean_transactions(spark)
    clean_shipments(spark)
    clean_products_scd2(spark)


# COMMAND ----------

# DBTITLE 1,Cell 2
spark.conf.set(
    f"fs.azure.account.key.iaspstorage3.dfs.core.windows.net",
    "<YOUR_ACCESS_KEY_HERE>"
)
run_silver_cleaning(spark)

# COMMAND ----------


display(
    spark.read.format("delta")
        .load(f"{SILVER_DIR}/inventory")
        )