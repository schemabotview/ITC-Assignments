from pyspark.sql import SparkSession


def filter_experienced(df, min_years=10):
    """Return only rows whose experience exceeds min_years. Pure + unit-testable."""
    return df.filter(df.experience > min_years)


if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("Sample Jenkins Spark Job") \
        .getOrCreate()

    data = [("Uttam", 30), ("Raj", 28), ("DataEng", 5)]
    df = spark.createDataFrame(data, ["name", "experience"])

    result_df = filter_experienced(df, min_years=10)

    result_df.show()

    # Example write (can be HDFS/S3)
    result_df.write.mode("overwrite").csv("/tmp/output/sample_job")

    spark.stop()