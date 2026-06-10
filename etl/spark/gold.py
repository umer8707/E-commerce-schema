"""
Gold layer: aggregate Silver orders into business metrics.
- revenue_by_day: total revenue and item count per day
- top_products: top 10 products by total revenue
- user_spending: total spend and order count per user
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from config import (  # noqa: E402
    AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY,
    SILVER_CONTAINER, GOLD_CONTAINER, TEMP_DIR,
)
from azure_utils import upload_dir, download_dir  # noqa: E402


def _silver(spark, name: str):
    local = f"{TEMP_DIR}/silver/{name}"
    download_dir(SILVER_CONTAINER, name, local, AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY)
    return spark.read.parquet(local)


def _upload_gold(df, name: str):
    local = f"{TEMP_DIR}/gold/{name}"
    shutil.rmtree(local, ignore_errors=True)
    df.coalesce(1).write.mode("overwrite").parquet(local)
    upload_dir(local, GOLD_CONTAINER, name, AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY)
    print(f"  → {df.count()} rows written to gold/{name}")


def main():
    spark = (
        SparkSession.builder.appName("Gold ETL").master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    orders = _silver(spark, "orders")

    # --- Revenue by day ---
    print("Aggregating revenue_by_day...")
    revenue_by_day = (
        orders.withColumn("date", F.to_date("order_date"))
        .groupBy("date")
        .agg(
            F.round(F.sum("subtotal"), 2).alias("total_revenue"),
            F.count("item_id").alias("total_items"),
        )
        .orderBy("date")
    )
    _upload_gold(revenue_by_day, "revenue_by_day")

    # --- Top 10 products by revenue ---
    print("Aggregating top_products...")
    top_products = (
        orders.groupBy("product_id", "product_name")
        .agg(
            F.round(F.sum("subtotal"), 2).alias("total_revenue"),
            F.sum("quantity").alias("total_sold"),
        )
        .orderBy(F.desc("total_revenue"))
        .limit(10)
    )
    _upload_gold(top_products, "top_products")

    # --- Total spend per user ---
    print("Aggregating user_spending...")
    user_spending = (
        orders.groupBy("user_id")
        .agg(
            F.round(F.sum("subtotal"), 2).alias("total_spent"),
            F.countDistinct("cart_id").alias("total_orders"),
        )
        .orderBy(F.desc("total_spent"))
    )
    _upload_gold(user_spending, "user_spending")

    spark.stop()
    print("Gold layer complete.")


if __name__ == "__main__":
    main()
