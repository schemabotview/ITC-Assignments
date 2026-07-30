import pytest
from pyspark.sql import SparkSession

from capstone.curated_transforms import (
    remove_duplicates,
    bucket_amount,
    normalize_amount,
    flag_high_risk,
)


@pytest.fixture(scope="session")
def spark():
    s = (
        SparkSession.builder.master("local[2]")
        .appName("capstone_transform_tests")
        .getOrCreate()
    )
    yield s
    s.stop()


def test_remove_duplicates(spark):
    df = spark.createDataFrame(
        [("TXN_1", 100.0), ("TXN_1", 100.0), ("TXN_2", 200.0)],
        ["transaction_id", "transaction_amount"],
    )
    assert remove_duplicates(df).count() == 2


def test_bucket_amount(spark):
    df = spark.createDataFrame(
        [("a", 50.0), ("b", 300.0), ("c", 1500.0), ("d", 5000.0)],
        ["transaction_id", "transaction_amount"],
    )
    got = {r["transaction_id"]: r["amt_bucket"] for r in bucket_amount(df).collect()}
    assert got == {"a": "low", "b": "medium", "c": "high", "d": "very_high"}


def test_normalize_amount_adds_log(spark):
    import math

    df = spark.createDataFrame([("a", 99.0)], ["transaction_id", "transaction_amount"])
    row = normalize_amount(df).collect()[0]
    assert "amt_log" in row and abs(row["amt_log"] - math.log1p(99.0)) < 1e-9


def test_flag_high_risk(spark):
    # cols needed: transaction_amount, txn_hour, daily_transaction_count
    df = spark.createDataFrame(
        [
            ("risky", 600.0, 2, 5),   # >500, hour<=5, velocity>3  -> 1
            ("daytime", 600.0, 14, 5),  # hour too late            -> 0
            ("small", 100.0, 2, 5),   # amount too small           -> 0
            ("slow", 600.0, 2, 1),    # velocity too low           -> 0
        ],
        ["transaction_id", "transaction_amount", "txn_hour", "daily_transaction_count"],
    )
    got = {r["transaction_id"]: r["high_risk"] for r in flag_high_risk(df).collect()}
    assert got == {"risky": 1, "daytime": 0, "small": 0, "slow": 0}
