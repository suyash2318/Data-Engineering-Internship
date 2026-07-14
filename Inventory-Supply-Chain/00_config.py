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