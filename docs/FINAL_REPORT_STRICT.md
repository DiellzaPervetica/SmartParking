# Smart Parking IoT - Raport Final

## 1. Hyrje

Qellimi i projektit eshte ndertimi i nje sistemi IoT funksional per Smart Parking, ku te dhenat e sensorit mblidhen, transmetohen, perpunohen ne kohe reale dhe ruhen ne menyre te organizuar. Domeni i zgjedhur eshte parkimi urban ne Prishtine, sepse perputhet direkt me problemet e mobilitetit urban: gjetja e vendeve te lira, ulja e qarkullimit te panevojshem dhe informimi i perdoruesve ne kohe reale.

Objektivat kryesore jane:

- simulimi i sensoreve ultrasonike per vende parkimi;
- transmetimi i eventeve ne Apache Kafka;
- procesimi ne kohe reale me Apache Spark Streaming;
- ruajtja e te dhenave te perpunuara ne Apache Cassandra;
- vizualizimi ne ueb i gjendjes se parkingut;
- zgjerimi me machine learning, alarme dhe cmim dinamik.

## 2. Infrastruktura e Projektit

Arkitektura praktike e sistemit eshte:

`Simulator i sensoreve -> MQTT Gateway -> Kafka -> Spark Streaming -> Cassandra -> FastAPI/Vue Dashboard`

Simulatori krijon lexime per cdo vend parkimi: `occupied`, `distance_cm`, `battery_level`, `signal_strength`, `timestamp`, `sensor_id`, `spot_id`, `gateway_id` dhe `event_type`. Gateway validon payload-in, e normalizon dhe e dergon ne Kafka. Spark Streaming eshte komponenti kryesor i procesimit real-time: konsumon topic-un raw, filtron te dhenat jo valide, llogarit metrika me dritare, aplikon AI dhe ruan rezultatet ne Cassandra. FastAPI ekspozon endpoint-e per dashboard-in, ndersa Vue paraqet parkingun, zonat, statusin e sensoreve, cmimin dinamik dhe alarmet.

## 3. Integrimi me Apache Kafka

Kafka perdoret si sistem transmetimi per eventet e sensorit. Topic-et kryesore jane:

- `parking.raw-events`: eventet e normalizuara nga gateway;
- `parking.processed-events`: evente te perpunuara nga Spark;
- `parking.sensor-alerts`: alarmet e validimit dhe anomalive;
- `parking.ai-input`: topic opsional per eksperimente AI te ndara.

Kafka topics krijohen me:

```powershell
python -m scripts.init_kafka_topics
```

Producer-i eshte `KafkaEventProducer`, i cili dergon payload-in ne `parking.raw-events`. Spark Streaming vepron si consumer zyrtar per procesim te metejme.

## 4. Procesimi me Apache Spark Streaming

Komponenti Spark gjendet ne `app/streaming/spark_streaming_processor.py`. Ai perdor Spark Structured Streaming per te lexuar nga Kafka:

- ben `from_json` mbi payload-in e sensorit;
- validon fushat kryesore;
- filtron lexime jashte intervaleve te lejuara;
- shton timestamp te ingestimit;
- krijon metrika me dritare 1-minuteshe;
- aplikon machine learning per prediction, anomaly detection dhe classification;
- llogarit cmimin dinamik;
- ruan rezultatet ne Cassandra.

Per te mos e renduar projektin, Spark perdor micro-batches cdo 10 sekonda dhe `spark.sql.shuffle.partitions=2`. Kjo eshte e mjaftueshme per nje parking prototip me 20 vende, por arkitektura mund te zgjerohet horizontalisht.

## 5. Ruajtja e te Dhenave ne Cassandra

Skema Cassandra gjendet ne `config/cassandra/init.cql`. Tabelat kryesore jane:

- `sensor_metadata_by_id`: metadata per sensorin, vendin, zonen dhe gateway;
- `sensor_events_by_spot`: historiku i eventeve per cdo vend parkimi;
- `current_spot_status`: gjendja aktuale e cdo vendi;
- `parking_summary_by_minute`: permbledhje e parkingut;
- `sensor_window_metrics_by_minute`: agregime nga Spark Streaming;
- `ai_results_by_time`: prediction, classification, anomaly dhe pricing;
- `alerts_by_time`: alarmet e sistemit.

Skema inicializohet me:

```powershell
python -m app.storage.migrations
```

## 6. Nderfaqja e Vizualizimit

Dashboard-i hapet ne:

```text
http://127.0.0.1:8000/dashboard
```

Ai paraqet:

- numrin e vendeve te lira;
- shkallen aktuale te okupimit;
- parashikimin per 30 minuta;
- cmimin dinamik;
- planin vizual te parkingut sipas zonave;
- gjendjen e sensoreve;
- pipeline-in Kafka/Spark/Cassandra/AI;
- alarmet dhe anomalite.

Endpoint-i `/parking/dashboard-data` lexon nga Cassandra kur pipeline-i live eshte aktiv. Nese Cassandra ende nuk ka te dhena, perdoret simulimi fallback vetem per te mbajtur dashboard-in funksional.

## 7. Komponentet e Avancuara

### Machine Learning

Projekti perfshin:

- Random Forest Regressor per parashikimin e okupimit, sepse Random Forest dhe regression jane pjese e materialit te mesuar;
- Decision Tree Classifier per detektimin/klasifikimin e gjendjes se sensorit, sepse decision trees, entropy/information gain dhe classification jane pjese e lendes;
- klasifikim te eventeve ne `free`, `occupied`, `suspicious`, `sensor_fault`;
- cmim dinamik si rregull aplikativ i bazuar ne okupim aktual, forecast dhe peak-hours. Ky nuk prezantohet si algoritëm i ri ML, por si vendimmarrje/utility e shtreses se aplikacionit.

### Sistemi i Alarmimeve

Alarmet gjenerohen per:

- bateri te ulet;
- sinjal te dobet;
- distance jo konsistente me statusin e vendit;
- gabime validimi;
- probleme runtime si sequence gap.

### Analiza e Performances dhe Optimizimi

Optimizimet kryesore jane:

- processing interval 10 sekonda per te shmangur ngarkesen e panevojshme;
- Spark checkpointing per tolerance ndaj nderprerjeve;
- Cassandra me tabela query-oriented;
- modele ML te lehta, te pershtatshme per demonstrim dhe prototip master;
- dashboard qe rifreskohet periodikisht pa polling agresiv.

Benchmark lokal per validim + ML mund te ekzekutohet me:

```powershell
python -m scripts.benchmark_pipeline
```

## 8. Hapat per Demonstrim Live

```powershell
.\scripts\start_strict_demo.ps1
```

Pastaj hapen kater terminale:

```powershell
python -m app.gateway.mqtt_consumer
python -m app.streaming.spark_streaming_processor
python -m app.simulator.run_simulator
uvicorn app.main:app --reload
```

Gjate mbrojtjes demonstrohet rrjedha:

1. simulatori prodhon te dhena sensori;
2. gateway i dergon ne Kafka;
3. Spark i perpunon ne kohe reale;
4. Cassandra ruan rezultatet;
5. dashboard-i i vizualizon.

## 9. Perfundime dhe Rekomandime

Projekti realizon nje sistem IoT funksional sipas kerkesave: mbledhje, transmetim, procesim real-time, ruajtje dhe vizualizim. Zgjerimi me AI eshte kufizuar ne koncepte te mesuara ne lende: supervised learning, regression, classification, decision trees, Random Forest, train/test evaluation dhe metrika performance. Per permiresime te ardhshme rekomandohen sensore fizike, deployment ne cloud, autentikim per dashboard-in dhe testim me ngarkese me te madhe.
