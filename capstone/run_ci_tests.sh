#!/usr/bin/env bash
# Runs the capstone transform unit tests on the Cloudera cluster.
# CDH ships pyspark under the parcel; put it on PYTHONPATH so `import pyspark`
# works from the system python3 (pytest 7.0.1 is already installed there).
set -e
export SPARK_HOME=/opt/cloudera/parcels/CDH/lib/spark
export PYTHONPATH="$SPARK_HOME/python:$(ls $SPARK_HOME/python/lib/py4j-*.zip)"
export PYSPARK_PYTHON=/usr/bin/python3
export JAVA_HOME=/usr/lib/jvm/java-11
cd "$(dirname "$0")/.."
python3 -m pytest capstone/tests/ -v
