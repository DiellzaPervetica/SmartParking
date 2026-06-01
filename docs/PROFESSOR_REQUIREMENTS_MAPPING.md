# Hartimi i kerkesave te profesorit me projektin

Ky dokument eshte liste kontrolli per prezantim. Projekti eshte pershtatur qe rrjedha kryesore te jete strikt sipas PDF-it te kursit "Internet of Things - Projekti 2".

| Kerkesa nga PDF | Implementimi ne projekt |
| --- | --- |
| Zgjedhja e domenit IoT | Smart Parking urban per nje parking ne Prishtine |
| Sensor fizik ose simulator | `app/simulator/run_simulator.py`, `vehicle_flow_simulator.py`, `ultrasonic_sensor_simulator.py` |
| Mbledhje te dhenash ne intervale te rregullta | Simulator me `SIMULATION_STEP_SECONDS` dhe `HEARTBEAT_SECONDS` |
| Transmetim ne Apache Kafka | `app/gateway/mqtt_consumer.py` validon MQTT dhe `KafkaEventProducer` dergon ne `parking.raw-events` |
| Kafka producer/topic | `app/gateway/kafka_producer.py`, `config/kafka/topics.env`, `scripts/init_kafka_topics.py` |
| Kafka consumer per procesim | `app/streaming/spark_streaming_processor.py` konsumon Kafka permes Spark Structured Streaming |
| Apache Spark Streaming | `read_valid_sensor_events`, `write_sensor_batch_to_cassandra`, `write_window_metrics_to_cassandra` |
| Agregime, validime, filtrime, dritare rreshqitese | Validim i fushave, filtrim i leximeve jo valide, metrika 1-minuteshe me watermark 2 minuta |
| Apache Cassandra Database | `config/cassandra/init.cql`, `app/storage/repositories.py` |
| Skeme per te dhena sensorike dhe metadata | `sensor_events_by_spot`, `current_spot_status`, `sensor_metadata_by_id` |
| Spark ruan te dhenat e perpunuara ne Cassandra | `foreachBatch` ne `spark_streaming_processor.py` ruan evente, status aktual, summary, window metrics, AI, alarme |
| Nderfaqe web per vizualizim | `/dashboard`, `app/static/index.html`, `app/static/app.js`, `app/static/styles.css` |
| Sistem funksional gjate mbrojtjes | `scripts/start_strict_demo.ps1` dhe fallback `/parking/dashboard-data` per rast pa Cassandra |
| Komponente te avancuara AI | Random Forest per prediction, Decision Tree Classifier per anomaly/classification, dynamic pricing si rregull aplikativ |
| Sistem alarmimesh | `alerts_by_time`, Kafka topic `parking.sensor-alerts`, `/ai/alerts/latest` |
| Analize performance/optimizim | Spark trigger i lehte, micro-batches 10s, checkpointing, `spark.sql.shuffle.partitions=2`, modelet ML te lehta, `scripts/benchmark_pipeline.py` |

## Rrjedha per demonstrim live

1. Simulatori gjeneron lexime te sensorit ultrasonik.
2. MQTT gateway validon dhe normalizon payload-in.
3. Gateway dergon eventet ne Kafka topic `parking.raw-events`.
4. Spark Streaming konsumon nga Kafka, filtron/validon dhe ben agregime me dritare.
5. Spark ruan ne Cassandra: evente, metadata, status aktual, summary, alarme dhe rezultate AI.
6. API lexon nga Cassandra dhe dashboard-i Vue vizualizon parkingun.
