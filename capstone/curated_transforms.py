"""Curation transforms for the CC-fraud capstone.

Pure DataFrame -> DataFrame functions so they can be unit-tested with a local
SparkSession (no cluster needed). The cluster job (curate.py) applies the same
logic; keeping them here lets Jenkins run pytest against them on every push.
"""
from pyspark.sql import functions as F


def remove_duplicates(df):
    """Drop duplicate transactions by transaction_id."""
    return df.dropDuplicates(["transaction_id"])


def handle_nulls(df):
    """Drop rows missing critical fields; fill missing amounts with 0."""
    return df.dropna(subset=["transaction_id", "fraud_label"]).fillna(
        {"transaction_amount": 0}
    )


def add_time_features(df):
    """Derive txn_hour / txn_day_of_week / txn_month from the timestamp."""
    return (
        df.withColumn("txn_hour", F.hour("timestamp"))
        .withColumn("txn_day_of_week", F.dayofweek("timestamp"))
        .withColumn("txn_month", F.month("timestamp"))
    )


def normalize_amount(df):
    """Add amt_log = log1p(transaction_amount)."""
    return df.withColumn("amt_log", F.log1p(F.col("transaction_amount")))


def bucket_amount(df):
    """Bucket transaction_amount into low / medium / high / very_high."""
    return df.withColumn(
        "amt_bucket",
        F.when(F.col("transaction_amount") < 100, "low")
        .when(F.col("transaction_amount") < 500, "medium")
        .when(F.col("transaction_amount") < 2000, "high")
        .otherwise("very_high"),
    )


def flag_high_risk(df):
    """Flag high_risk = big amount AND small hours (<=5) AND high daily velocity."""
    return df.withColumn(
        "high_risk",
        (
            (F.col("transaction_amount") > 500)
            & (F.col("txn_hour") <= 5)
            & (F.col("daily_transaction_count") > 3)
        ).cast("int"),
    )
