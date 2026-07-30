import pytest
from pyspark.sql import SparkSession

from src.transformation import filter_experienced


@pytest.fixture(scope="session")
def spark():
    s = (
        SparkSession.builder
        .master("local[2]")
        .appName("day9_ganesh_unit_test")
        .getOrCreate()
    )
    yield s
    s.stop()


def test_keeps_only_experience_over_threshold(spark):
    data = [("Uttam", 30), ("Raj", 28), ("DataEng", 5)]
    df = spark.createDataFrame(data, ["name", "experience"])

    result = filter_experienced(df, min_years=10)

    names = sorted(r["name"] for r in result.collect())
    assert names == ["Raj", "Uttam"]   # 5 <= 10 is dropped


def test_threshold_is_strict_greater_than(spark):
    data = [("Exactly10", 10), ("Eleven", 11)]
    df = spark.createDataFrame(data, ["name", "experience"])

    result = filter_experienced(df, min_years=10)

    names = [r["name"] for r in result.collect()]
    assert names == ["Eleven"]   # boundary value 10 is excluded
