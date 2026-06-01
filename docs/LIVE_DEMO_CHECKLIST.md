# Checklist per mbrojtje

## Para prezantimit

- Docker Desktop eshte i ndezur.
- `pip install -r requirements.txt` eshte ekzekutuar.
- `.\scripts\start_strict_demo.ps1` perfundon pa gabime.
- Dashboard hapet ne `http://127.0.0.1:8000/dashboard`.
- `/docs` hap Swagger UI te FastAPI.

## Demonstrimi live

1. Trego domenin: Smart Parking.
2. Trego simulatorin: `python -m app.simulator.run_simulator`.
3. Trego Kafka topic-et: `parking.raw-events`, `parking.processed-events`, `parking.sensor-alerts`.
4. Trego Spark Streaming: `python -m app.streaming.spark_streaming_processor`, ose `.\scripts\run_spark_in_docker.ps1` nese Java mungon lokalisht.
5. Trego Cassandra schema: `config/cassandra/init.cql`.
6. Trego dashboard-in Vue.
7. Trego ML: Random Forest prediction, Decision Tree sensor classification/anomaly, dhe dynamic pricing si rregull aplikativ.
8. Trego alarmet: skenari `maintenance` ose lexime me bateri/sinjal te dobet.

## Pyetje te mundshme

- Pse Kafka? Sepse ndan prodhimin e eventeve nga procesimi dhe lejon streaming ne kohe reale.
- Pse Spark Streaming? Sepse proceson stream-in nga Kafka me validime, filtrime dhe dritare kohore.
- Pse Cassandra? Sepse te dhenat IoT jane append-heavy dhe query-oriented sipas sensorit/kohes.
- Pse ML eshte i lehte? Sepse projekti eshte prototip master dhe duhet te jete funksional ne laptop.
