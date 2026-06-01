# Spark Streaming configuration

The project uses PySpark Structured Streaming from `app.streaming.spark_streaming_processor`.

Default local settings:

```text
SPARK_MASTER_URL=local[*]
SPARK_TRIGGER_SECONDS=10
SPARK_KAFKA_PACKAGE=org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1
SPARK_CHECKPOINT_DIR=data/checkpoints/spark
```

For a Docker Spark master, set:

```powershell
$env:SPARK_MASTER_URL="spark://localhost:7077"
```

For the live defense demo, local mode is simpler and lighter, while still using Apache Spark Streaming.

If Java is not installed on Windows, run Spark inside Docker:

```powershell
.\scripts\run_spark_in_docker.ps1
```
