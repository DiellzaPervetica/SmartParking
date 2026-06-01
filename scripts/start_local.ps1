Write-Host "Starting Docker services: MQTT, Kafka, Spark, Cassandra..."
docker compose -f docker/docker-compose.yml up -d

Write-Host "Waiting 25 seconds for services to warm up..."
Start-Sleep -Seconds 25

Write-Host "Initializing Kafka topics..."
python -m scripts.init_kafka_topics

Write-Host "Initializing Cassandra schema..."
python -m app.storage.migrations

Write-Host "Seeding historical data..."
python -m scripts.seed_historical_data

Write-Host "Training AI models..."
python -m app.ai.train_models

Write-Host ""
Write-Host "Strict live-demo pipeline. Start these in separate terminals:"
Write-Host "python -m app.gateway.mqtt_consumer"
Write-Host "python -m app.streaming.spark_streaming_processor"
Write-Host "If Java is missing locally: .\scripts\run_spark_in_docker.ps1"
Write-Host "python -m app.simulator.run_simulator"
Write-Host "uvicorn app.main:app --reload"
Write-Host ""
Write-Host "Dashboard: http://127.0.0.1:8000/dashboard"
