$projectRoot = Resolve-Path "$PSScriptRoot\.."

Write-Host "Starting Spark Streaming inside Docker."
Write-Host "This uses container networking: Kafka=kafka:29092, Cassandra=cassandra."

docker compose -f "$projectRoot\docker\docker-compose.yml" run --rm `
  --entrypoint bash `
  -v "$projectRoot`:/workspace" `
  -w /workspace `
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 `
  -e CASSANDRA_HOSTS=cassandra `
  -e SPARK_MASTER_URL=local[*] `
  -e SPARK_CHECKPOINT_DIR=data/checkpoints/spark-docker `
  spark-master `
  -lc "pip install -r requirements.txt && python -m app.streaming.spark_streaming_processor"
