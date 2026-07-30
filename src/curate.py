from pyspark.sql import SparkSession, functions as F

spark = (SparkSession.builder
        .appName("ganesh_capstone_curate")
        .enableHiveSupport()
        .getOrCreate())

df = spark.table("ganesh_db.cc_fraud_raw")
print("RAW COUNT:", df.count())

# 1. remove duplicate transactions
df = df.dropDuplicates(["transaction_id"])

# 2. handle nulls: drop rows missing critical fields, fill amount nulls
df = df.dropna(subset=["transaction_id", "fraud_label"]).fillna({"transaction_amount": 0})

# 3. time features from the timestamp
df = (df.withColumn("txn_hour",        F.hour("timestamp"))
        .withColumn("txn_day_of_week", F.dayofweek("timestamp"))
        .withColumn("txn_month",       F.month("timestamp")))

# 4. normalize amount (log1p)
df = df.withColumn("amt_log", F.log1p(F.col("transaction_amount")))

# 5. bucket amount
df = df.withColumn("amt_bucket",
        F.when(F.col("transaction_amount") < 100,  "low")
        .when(F.col("transaction_amount") < 500,  "medium")
        .when(F.col("transaction_amount") < 2000, "high")
        .otherwise("very_high"))

# 6. flag high-risk: big amount, small hours, high daily velocity
df = df.withColumn("high_risk",
        ((F.col("transaction_amount") > 500) &
        (F.col("txn_hour") <= 5) &
        (F.col("daily_transaction_count") > 3)).cast("int"))

print("CURATED COUNT:", df.count())

(df.write.mode("overwrite").format("hive")
    .saveAsTable("ganesh_db.cc_fraud_curated"))
print("WROTE ganesh_db.cc_fraud_curated")
spark.stop()
