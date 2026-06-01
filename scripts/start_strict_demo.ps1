Write-Host "Smart Parking strict demo startup"
Write-Host "1. Infrastructure: Kafka, Spark, Cassandra, MQTT"
docker compose -f docker/docker-compose.yml up -d

Write-Host "2. Waiting for containers..."
Start-Sleep -Seconds 25

Write-Host "3. Kafka topics"
python -m scripts.init_kafka_topics

Write-Host "4. Cassandra schema"
python -m app.storage.migrations

Write-Host "5. Historical data and ML models"
python -m scripts.seed_historical_data
python -m app.ai.train_models

Write-Host ""
Write-Host "Open four PowerShell terminals and run:"
Write-Host "A) python -m app.gateway.mqtt_consumer"
Write-Host "B) python -m app.streaming.spark_streaming_processor"
Write-Host "   If Java is missing locally, run instead: .\scripts\run_spark_in_docker.ps1"
Write-Host "C) python -m app.simulator.run_simulator"
Write-Host "D) uvicorn app.main:app --reload"
Write-Host ""
Write-Host "Then open: http://127.0.0.1:8000/dashboard"
