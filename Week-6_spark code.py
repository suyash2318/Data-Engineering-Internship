"""
Data Engineering Week 6 - Spark Assignment
PySpark Solution: Architecture + Data Processing Pipeline
"""

# ============================================================
# SECTION 1: SPARK ARCHITECTURE OVERVIEW (Comments/Docstrings)
# ============================================================

"""
SPARK ARCHITECTURE:
-------------------
1. Driver Program  : Entry point; hosts SparkContext; orchestrates execution.
2. Cluster Manager : Allocates resources (YARN / Mesos / Standalone / K8s).
3. Executors       : JVM processes on worker nodes; run tasks, cache data.

EXECUTION MODES:
- Local[*]     : All components on one JVM (dev/testing).
- Client Mode  : Driver runs on submitting machine (interactive use).
- Cluster Mode : Driver runs inside the cluster (production).

LAZY EVALUATION & DAG:
- Transformations (map, filter, select) are lazy — not executed immediately.
- Spark builds a DAG (Directed Acyclic Graph) of transformations.
- Execution triggers only on an Action (show, count, write, collect).
- Catalyst Optimizer rewrites the DAG for optimal execution (predicate pushdown, etc.).
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType,
    IntegerType, FloatType, DateType
)
import os

# ============================================================
# SECTION 2: SPARK SESSION INITIALIZATION
# ============================================================

spark = SparkSession.builder \
    .appName("DataEngineering003_SparkAssignment") \
    .master("local[*]") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print("✅ SparkSession created | Version:", spark.version)
print("=" * 65)

# ============================================================
# SECTION 3: DEFINE SCHEMA & CREATE SAMPLE DATA
# ============================================================

schema = StructType([
    StructField("emp_id",        IntegerType(), True),
    StructField("emp_name",      StringType(),  True),
    StructField("department",    StringType(),  True),
    StructField("salary",        FloatType(),   True),
    StructField("join_date",     StringType(),  True),
    StructField("city",          StringType(),  True),
    StructField("experience_yr", IntegerType(), True),
])

data = [
    (101, "Suyash Maheshwari",    "Engineering",  85000.0, "2021-06-15", "Jaipur",   3),
    (102, "Priya Mehra",      "Data Science", 92000.0, "2020-03-10", "Bangalore",5),
    (103, "Rahul Verma",      "Engineering",  78000.0, "2022-01-20", "Delhi",    2),
    (104, "Ananya Singh",     "HR",           55000.0, "2019-07-01", "Mumbai",   6),
    (105, "Karan Joshi",      "Data Science", 110000.0,"2018-11-05", "Hyderabad",7),
    (106, "Divya Patel",      "Engineering",  88000.0, "2021-09-30", "Pune",     4),
    (107, "Arjun Nair",       "Finance",      67000.0, "2020-12-15", "Chennai",  4),
    (108, None,               "Engineering",  72000.0, "2023-03-01", "Jaipur",   1),
    (109, "Meera Iyer",       "Data Science", None,    "2022-08-18", "Bangalore",2),
    (110, "Vikram Chauhan",   "HR",           51000.0, "2017-04-22", "Delhi",    8),
]

df = spark.createDataFrame(data, schema=schema)

print("📋 RAW DATASET (original):")
df.show(truncate=False)
df.printSchema()

# ============================================================
# SECTION 4: NULL HANDLING
# ============================================================
print("=" * 65)
print("🔍 NULL VALUE ANALYSIS:")
null_counts = df.select([
    F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns
])
null_counts.show()

# Drop rows with null emp_name; fill null salary with dept median logic (simplified: fill with 80000)
df_clean = df.dropna(subset=["emp_name"]) \
             .fillna({"salary": 80000.0})

print("✅ After null handling:")
df_clean.show(truncate=False)

# ============================================================
# SECTION 5: SELECT, FILTER, RENAME COLUMNS
# ============================================================
print("=" * 65)
print("🔎 FILTERING: Engineering dept, salary > 80000:")

df_filtered = df_clean \
    .filter((F.col("department") == "Engineering") & (F.col("salary") > 80000)) \
    .select("emp_id", "emp_name", "department", "salary", "city")

df_filtered.show(truncate=False)

# Rename columns
df_renamed = df_clean \
    .withColumnRenamed("emp_name", "employee_name") \
    .withColumnRenamed("experience_yr", "years_of_experience")

print("✏️  After column rename:")
df_renamed.select("emp_id", "employee_name", "years_of_experience").show()

# ============================================================
# SECTION 6: ADD NEW COLUMNS & CAST DATA TYPES
# ============================================================
print("=" * 65)
print("➕ ADDING COMPUTED COLUMNS:")

df_transformed = df_clean \
    .withColumn("salary_grade", F.when(F.col("salary") >= 90000, "A")
                                  .when(F.col("salary") >= 70000, "B")
                                  .otherwise("C")) \
    .withColumn("annual_bonus", F.round(F.col("salary") * 0.10, 2)) \
    .withColumn("total_comp",   F.round(F.col("salary") + F.col("salary") * 0.10, 2)) \
    .withColumn("join_year",    F.year(F.to_date(F.col("join_date"), "yyyy-MM-dd")))

df_transformed.select(
    "emp_id", "emp_name", "salary", "salary_grade", "annual_bonus", "total_comp", "join_year"
).show(truncate=False)

# ============================================================
# SECTION 7: AGGREGATIONS (WIDE TRANSFORMATION — SHUFFLE)
# ============================================================
print("=" * 65)
print("📊 AGGREGATION BY DEPARTMENT (triggers shuffle):")

dept_stats = df_transformed.groupBy("department") \
    .agg(
        F.count("emp_id").alias("headcount"),
        F.round(F.avg("salary"), 2).alias("avg_salary"),
        F.max("salary").alias("max_salary"),
        F.min("salary").alias("min_salary"),
        F.round(F.sum("total_comp"), 2).alias("total_compensation")
    ) \
    .orderBy("avg_salary", ascending=False)

dept_stats.show(truncate=False)

# ============================================================
# SECTION 8: WINDOW FUNCTIONS
# ============================================================
print("=" * 65)
print("🪟 WINDOW FUNCTION — Salary Rank within Department:")

from pyspark.sql.window import Window

window_spec = Window.partitionBy("department").orderBy(F.desc("salary"))
df_ranked = df_transformed \
    .withColumn("dept_salary_rank", F.rank().over(window_spec))

df_ranked.select("emp_id", "emp_name", "department", "salary", "dept_salary_rank") \
         .orderBy("department", "dept_salary_rank") \
         .show(truncate=False)

# ============================================================
# SECTION 9: SAVE AS CSV AND PARQUET
# ============================================================
print("=" * 65)
print("💾 WRITING OUTPUT FILES:")

out_csv     = "/home/claude/output/employees_csv"
out_parquet = "/home/claude/output/employees_parquet"
out_agg_csv = "/home/claude/output/dept_stats_csv"

df_transformed.coalesce(1).write.mode("overwrite").option("header", True).csv(out_csv)
df_transformed.coalesce(1).write.mode("overwrite").parquet(out_parquet)
dept_stats.coalesce(1).write.mode("overwrite").option("header", True).csv(out_agg_csv)

print(f"✅ CSV written     → {out_csv}")
print(f"✅ Parquet written → {out_parquet}")
print(f"✅ Dept stats CSV  → {out_agg_csv}")

# ============================================================
# SECTION 10: VERIFY RE-READ FROM PARQUET
# ============================================================
print("=" * 65)
print("🔁 RE-READ FROM PARQUET (verifying schema preservation):")
df_parquet = spark.read.parquet(out_parquet)
df_parquet.printSchema()
df_parquet.select("emp_id", "emp_name", "salary_grade", "total_comp").show(5)

print("=" * 65)
print("✅ Spark Assignment Complete!")
spark.stop()
