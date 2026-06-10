"""
Bronze layer: extract raw data from PostgreSQL and store as Parquet in Azure Blob Storage.
Each table is written to azure://bronze/<table>/ingestion_date=YYYY-MM-DD/
"""
import os
import sys
import shutil
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from config import DATABASE_URL, AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY, BRONZE_CONTAINER, TEMP_DIR  # noqa: E402
from azure_utils import upload_dir  # noqa: E402

TABLES = ["users", "products", "carts", "cart_items"]
TODAY = date.today().isoformat()
CHUNK_SIZE = 50_000


def read_table(engine, table: str) -> pd.DataFrame:
    chunks = []
    for chunk in pd.read_sql(f"SELECT * FROM {table}", engine, chunksize=CHUNK_SIZE):
        chunks.append(chunk)
        print(f"    read {sum(len(c) for c in chunks):,} rows...", end="\r")
    return pd.concat(chunks, ignore_index=True)


def main():
    spark = (
        SparkSession.builder.appName("Bronze ETL").master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    engine = create_engine(DATABASE_URL)
    try:
        for table in TABLES:
            print(f"Extracting {table}...")
            pdf = read_table(engine, table)
            print(f"    loaded {len(pdf):,} rows, converting to Spark...")

            df = spark.createDataFrame(pdf)
            df = df.withColumn("ingestion_date", F.lit(TODAY))

            local_out = f"{TEMP_DIR}/bronze/{table}"
            shutil.rmtree(local_out, ignore_errors=True)
            df.coalesce(1).write.mode("overwrite").parquet(local_out)

            upload_dir(
                local_dir=local_out,
                container=BRONZE_CONTAINER,
                prefix=f"{table}/ingestion_date={TODAY}",
                account=AZURE_STORAGE_ACCOUNT,
                key=AZURE_STORAGE_KEY,
            )
            print(f"  → {len(pdf):,} rows written to bronze/{table}")
    finally:
        engine.dispose()
        spark.stop()

    print("Bronze layer complete.")


if __name__ == "__main__":
    main()
