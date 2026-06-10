"""
Silver layer: clean and join Bronze data, write to Azure Silver container.
- users: remove nulls, deduplicate
- products: remove nulls, filter invalid prices/stock
- orders: join checked_out carts with cart_items
"""
import os
import sys
import shutil
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from config import (  # noqa: E402
    AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY,
    BRONZE_CONTAINER, SILVER_CONTAINER, TEMP_DIR,
)
from azure_utils import upload_dir, download_dir  # noqa: E402

TODAY = date.today().isoformat()


def _bronze(spark, table: str):
    local = f"{TEMP_DIR}/bronze/{table}"
    download_dir(BRONZE_CONTAINER, f"{table}/ingestion_date={TODAY}", local,
                 AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY)
    return spark.read.parquet(local)


def _upload_silver(df, name: str):
    local = f"{TEMP_DIR}/silver/{name}"
    shutil.rmtree(local, ignore_errors=True)
    df.coalesce(1).write.mode("overwrite").parquet(local)
    upload_dir(local, SILVER_CONTAINER, name, AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY)
    print(f"  → {df.count()} rows written to silver/{name}")


def main():
    spark = (
        SparkSession.builder.appName("Silver ETL").master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # --- Users ---
    print("Processing users...")
    users = _bronze(spark, "users")
    users = (
        users.dropna(subset=["id", "email"])
        .dropDuplicates(["id"])
        .select("id", "name", "email", "created_at", "ingestion_date")
    )
    _upload_silver(users, "users")

    # --- Products ---
    print("Processing products...")
    products = _bronze(spark, "products")
    products = (
        products.dropna(subset=["id", "price"])
        .dropDuplicates(["id"])
        .filter(F.col("price") > 0)
        .filter(F.col("stock") >= 0)
        .select("id", "name", "price", "stock", "created_at", "ingestion_date")
    )
    _upload_silver(products, "products")

    # --- Orders (checked_out carts joined with cart_items) ---
    print("Processing orders...")
    carts = _bronze(spark, "carts")
    cart_items = _bronze(spark, "cart_items")
    checked_out = carts.filter(F.col("status") == "checked_out")
    orders = checked_out.join(
        cart_items, checked_out["id"] == cart_items["cart_id"], "inner"
    ).select(
        cart_items["id"].alias("item_id"),
        checked_out["id"].alias("cart_id"),
        checked_out["user_id"],
        cart_items["product_id"],
        cart_items["product_name"],
        cart_items["quantity"],
        cart_items["price"],
        cart_items["subtotal"],
        checked_out["created_at"].alias("order_date"),
        checked_out["ingestion_date"],
    )
    _upload_silver(orders, "orders")

    spark.stop()
    print("Silver layer complete.")


if __name__ == "__main__":
    main()
