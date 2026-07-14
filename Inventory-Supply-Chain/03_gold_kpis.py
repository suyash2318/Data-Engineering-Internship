# Databricks notebook source
# DBTITLE 1,Cell 1
from pyspark.sql.functions import col, sum, avg, count, when, lit, year, month
storage_account = "iaspstorage3"
container = "iaspcontainer"

BASE_PATH = f"abfss://{container}@{storage_account}.dfs.core.windows.net"
RAW_DIR = f"{BASE_PATH}/raw"
BRONZE_DIR = f"{BASE_PATH}/bronze"
SILVER_DIR = f"{BASE_PATH}/silver"
GOLD_DIR = f"{BASE_PATH}/gold"
CHECKPOINT_DIR = f"{BASE_PATH}/checkpoints"
SCHEMA_DIR = f"{BASE_PATH}/schema"



def _read_silver(spark, table):
    """Shorthand for reading a silver Delta table."""
    return spark.read.format("delta").load(f"{SILVER_DIR}/{table}")


def _save_gold(df, table_name):
    """Write a gold DataFrame and print the row count."""
    gold_path = f"{GOLD_DIR}/{table_name}"
    df.write.format("delta").mode("overwrite").save(gold_path)
    print(f"Gold {table_name} table saved. Rows: {df.count()}")


def build_inventory_snapshot(spark):
    """Join inventory + products + warehouses to get a full inventory picture with value."""
    inv = _read_silver(spark, "inventory")
    prod = _read_silver(spark, "products").filter(col("current_flag") == "Y")
    wh = _read_silver(spark, "warehouses")

    df = inv.join(prod, "product_id").join(wh, "warehouse_id")

    df = df.withColumn("inventory_value", col("available_stock") * col("selling_price")) \
           .select(
               "inventory_id", "product_id", "product_name", "category",
               "warehouse_id", "warehouse_name", "location_city",
               "stock_quantity", "reserved_quantity", "damaged_quantity",
               "available_stock", "selling_price", "inventory_value"
           )

    _save_gold(df, "inventory_snapshot")


def build_low_stock_alert(spark):
    """Flag products where available stock is below the reorder level."""
    inv = _read_silver(spark, "inventory")
    prod = _read_silver(spark, "products").filter(col("current_flag") == "Y")

    df = inv.join(prod, "product_id") \
            .filter(col("available_stock") < col("reorder_level")) \
            .withColumn(
                "alert_level",
                when(col("available_stock") == 0, lit("CRITICAL"))
                .when(col("available_stock") < (col("reorder_level") * 0.25), lit("HIGH"))
                .otherwise(lit("MEDIUM"))
            ).select(
                "inventory_id", "product_id", "product_name",
                "warehouse_id", "available_stock", "reorder_level", "alert_level"
            )

    _save_gold(df, "low_stock_alert")


def build_product_movement(spark):
    """Aggregate IN vs OUT transaction quantities per product."""
    tx = _read_silver(spark, "transactions")
    prod = _read_silver(spark, "products").filter(col("current_flag") == "Y")

    df = tx.groupBy("product_id").agg(
        sum(when(col("transaction_type") == "IN", col("quantity")).otherwise(0)).alias("total_stock_in"),
        sum(when(col("transaction_type") == "OUT", col("quantity")).otherwise(0)).alias("total_stock_out")
    ).withColumn("net_movement", col("total_stock_in") - col("total_stock_out"))

    df = df.join(prod.select("product_id", "product_name", "category"), "product_id")
    _save_gold(df, "product_movement")


def build_supplier_performance(spark):
    """Rate suppliers by average shipment delay."""
    shipments = _read_silver(spark, "shipments")
    suppliers = _read_silver(spark, "suppliers")

    df = shipments.groupBy("supplier_id").agg(
        avg("delay_days").alias("avg_delay"),
        count("shipment_id").alias("total_shipments")
    ).withColumn(
        "performance_category",
        when(col("avg_delay") <= 2.0, lit("EXCELLENT"))
        .when(col("avg_delay") <= 4.0, lit("GOOD"))
        .otherwise(lit("NEEDS IMPROVEMENT"))
    )

    df = df.join(suppliers.select("supplier_id", "supplier_name", "contact_email", "rating"), "supplier_id")
    _save_gold(df, "supplier_performance")


def build_sales_summary(spark):
    """Total revenue and units sold per product (OUT transactions only)."""
    tx = _read_silver(spark, "transactions")
    prod = _read_silver(spark, "products").filter(col("current_flag") == "Y")

    df = tx.filter(col("transaction_type") == "OUT") \
           .groupBy("product_id") \
           .agg(
               sum("quantity").alias("total_units_sold"),
               sum("total_price").alias("total_revenue")
           )

    df = df.join(prod.select("product_id", "product_name", "category", "selling_price"), "product_id")
    _save_gold(df, "sales_summary")


def build_sales_trend(spark):
    """Monthly revenue breakdown for trend analysis."""
    tx = _read_silver(spark, "transactions")

    df = tx.filter(col("transaction_type") == "OUT") \
           .withColumn("year", year(col("transaction_timestamp"))) \
           .withColumn("month", month(col("transaction_timestamp"))) \
           .groupBy("year", "month") \
           .agg(sum("total_price").alias("monthly_revenue")) \
           .orderBy("year", "month")

    _save_gold(df, "sales_trend")


def run_gold_kpis(spark):
    """Build all Gold layer KPI tables."""
    os.makedirs(GOLD_DIR, exist_ok=True)

    build_inventory_snapshot(spark)
    build_low_stock_alert(spark)
    build_product_movement(spark)
    build_supplier_performance(spark)
    build_sales_summary(spark)
    build_sales_trend(spark)

# COMMAND ----------

# DBTITLE 1,Cell 2
import os
spark.conf.set(
    f"fs.azure.account.key.iaspstorage3.dfs.core.windows.net",
    "<YOUR_ACCESS_KEY_HERE>"
)
run_gold_kpis(spark)

# COMMAND ----------

display(
        spark.read.format("delta")
            .load(f"{GOLD_DIR}/sales_summary")
            )
