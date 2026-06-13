# Smart Parking IoT - Raporti Final

## 1. Hyrje

Ky dokument permbledh punen e bere ne projektin Smart Parking Prishtina dhe e shpjegon rrjedhen e plote te sistemit:

```text
Sensor simulator -> MQTT Gateway -> Kafka -> Spark Streaming -> Cassandra -> FastAPI/Vue Dashboard
```

Qellimi kryesor eshte te demonstrohet nje sistem IoT qe:

- mbledh te dhena nga sensore te simuluar;
- i transmeton ne kohe reale;
- i perpunon me Spark Streaming;
- i ruan ne Apache Cassandra;
- i vizualizon ne nje dashboard web te lexueshem;
- gjeneron edhe analiza shtese si anomaly detection, prediction dhe dynamic pricing.

Ky raport eshte shkruar qe te perputhet me kerkesat e profesorit dhe te jete gati per dorzim si dokumentacion final.

## 2. Perkufizimi i problemit

Sistemi modelon nje parking urban ne Prishtine me 20 vende dhe dy zona kryesore. Ideja eshte qe secili vend parkimi te kete nje sensor ultrasonik te simuluar, i cili dergon periodikisht gjendjen e vendit:

- a eshte i zene apo i lire;
- sa eshte distanca e matur;
- sa eshte bateria;
- sa eshte forca e sinjalit;
- a eshte ngjarje e tipit `state_change` ose `heartbeat`.

Keto te dhena kalojne ne nje pipeline real-time qe lejon:

- shperndarjen e eventeve me Kafka;
- filtrimin dhe agregimin me Spark Streaming;
- ruajtjen historike me Cassandra;
- paraqitjen ne dashboard per demo dhe mbrojtje.

## 3. Arkitektura e sistemit

```text
1. Simulatori gjeneron payload per secilin vend parkimi.
2. Payload dergohet permes MQTT te gateway.
3. Gateway e validon dhe e normalizon payload-in.
4. Gateway e dergon eventin ne Kafka topic `parking.raw-events`.
5. Spark Streaming e lexon stream-in nga Kafka.
6. Spark filtron vlerat jo valide, llogarit metrika dhe i ruan ne Cassandra.
7. FastAPI lexon te dhenat nga Cassandra.
8. Vue dashboard i paraqet te dhenat ne forme vizuale.
```

### Roli i secilit komponent

- `app/simulator/` gjeneron ngarkesen e te dhenave per parkingun.
- `app/mqtt_layer/` nderton dhe dergon payload-et MQTT.
- `app/gateway/` validon, normalizon dhe i con eventet ne Kafka.
- `app/streaming/` perpunon eventet me Spark Streaming.
- `app/storage/` ruan te dhenat ne Cassandra.
- `app/services/` nderton snapshot-in qe lexon dashboard-i.
- `app/static/` permban dashboard-in dhe faqen e lokacioneve.

## 4. Mbledhja e te Dhenave

Mbledhja e te dhenave behet ne `app/simulator/run_simulator.py`. Simulatori iteron mbi te gjitha vendet e parkingut dhe per secilin vend gjeneron nje payload te ri kur:

- ka ndryshim gjendjeje (`state_change`);
- ose ka kaluar intervali i heartbeat-it (`heartbeat`).

### Frekuenca e gjenerimit

- `SIMULATION_STEP_SECONDS=5`
- `HEARTBEAT_SECONDS=30`

Kjo do te thote qe sistemi prodhon te dhena ne intervale te shkurtra dhe mban rrjedhe te vazhdueshme edhe kur nuk ka ndryshim ne zene/lire.

### Fushat qe mbledhen

| Fusha | Pershkrimi |
| --- | --- |
| `event_id` | Identifikues unik i eventit |
| `parking_id` | ID e parkingut |
| `parking_name` | Emri i parkingut |
| `zone_id` | Zona ku ndodhet vendi |
| `spot_id` | Identifikuesi i vendit parkues |
| `sensor_id` | Identifikuesi i sensorit |
| `gateway_id` | Identifikuesi i gateway |
| `sequence_no` | Numer rendor i eventit |
| `timestamp` | Koha kur u krijua leximi |
| `occupied` | A eshte vendi i zene |
| `distance_cm` | Distanca e matur nga sensori |
| `battery_level` | Niveli i baterise |
| `signal_strength` | Forca e sinjalit |
| `event_type` | `state_change` ose `heartbeat` |
| `ingest_ts` | Koha kur e mori gateway |

### Si prodhohet payload-i

Payload-i ndertohet ne `app/mqtt_layer/payload_builder.py`. Kjo eshte e rendesishme sepse raporti duhet te tregoje qarte qe te dhenat nuk merren nga nje database, por prodhohen nga nje simulator i kontrolluar.

### Si lexohet kjo pjese ne raport

Kur e shpjegon kete seksion, thuaj:

> Simulatori i parkingut gjeneron telemetri reale-ish per cdo vend parkimi. Keto lexime perfshijne zene/lire, distance, bateri dhe sinjal. Te dhenat dergohen ne menyre periodike qe te simulohet sjellja e nje sistemi IoT te vertete.

## 5. Transmetimi permes Kafka

Gateway MQTT i pranon payload-et, i kontrollon dhe pastaj i dergon ne Kafka. Kjo e ndan qarte shtresen e mbledhjes se te dhenave nga shtresa e procesimit.

### Validimi dhe normalizimi

Ne `app/gateway/mqtt_consumer.py` ndodhin keto hapa:

1. payload-i lexohet nga MQTT;
2. kontrollohet me `validate_sensor_payload`;
3. nese eshte i pasakte, krijohet alarm validimi;
4. nese eshte i sakte, normalizohet me `normalize_payload`;
5. monitorohet edhe gjendja runtime per anomali si `sequence_gap` ose `stuck_sensor`;
6. eventi dergohet ne Kafka.

### Kafka topics

| Topic | Roli |
| --- | --- |
| `parking.raw-events` | Eventet e para, te normalizuara nga gateway |
| `parking.processed-events` | Eventet e perpunuara nga Spark |
| `parking.sensor-alerts` | Alarme per validim dhe anomali |
| `parking.ai-input` | Topic ndihmes per eksperimente ose integrime AI |

### Si ta shpjegosh kete pjese

Thuaj qe Kafka sherben si bufer dhe kanal i besueshem transmetimi:

> Kafka e ndan producer-in nga consumer-i. Gateway shkruan ne topic-un raw, ndersa Spark e konsumon me vone. Kjo e ben sistemin me te qendrueshem dhe me te lehte per t'u zgjeruar.

### Komanda per krijimin e topic-eve

```powershell
python -m scripts.init_kafka_topics
```

## 6. Perpunimi me Spark Streaming

Spark Streaming eshte zemra e procesimit ne kohe reale. Implementimi gjendet ne `app/streaming/spark_streaming_processor.py`.

### Cfare ben Spark

- lexon eventet nga topic-u `parking.raw-events`;
- i pars-on si JSON me schema te percaktuar;
- filtron vlerat jo valide;
- shton timestamp-in e ingestimit;
- krijon evente te perpunuara dhe i shkruan ne `parking.processed-events`;
- ruan eventet ne Cassandra;
- llogarit agregime me dritare kohore;
- ekzekuton parashikim, klasifikim, anomaly detection dhe dynamic pricing.

### Rregullat e filtrimit

Spark i pranon vetem eventet qe:

- kane `parking_id`, `spot_id`, `sensor_id` dhe `event_ts` te vlefshem;
- kane `distance_cm` ne intervalin 0-500;
- kane `battery_level` ne intervalin 0-100;
- kane `signal_strength` ne intervalin -120 deri 0.

### Agregimet me dritare

Spark llogarit metrika me:

- dritare 1-minuteshe;
- watermark 2 minuta.

Keto metrika perfshijne:

- numrin e eventeve;
- numrin e eventeve ku vendi eshte i zene;
- mesataren e distances;
- mesataren e baterise;
- numrin e rasteve me sinjal te dobet.

### AI dhe logjika shtese

Spark perdor edhe modulet:

- `OccupancyPredictor`
- `SensorAnomalyDetector`
- `EventClassifier`
- `DynamicPricingEngine`

Kjo do te thote qe ne te njejtin batch sistemi:

- parashikon okupimin per 30 minuta;
- klasifikon vendin si `free`, `occupied`, `suspicious` ose `sensor_fault`;
- detekton anomali si `low_battery`, `signal_weak`, `distance_outlier`, `sequence_gap`;
- llogarit cmimin dinamik sipas okupimit dhe forecast-it.

### Optimizimi

Per ta mbajtur projektin te lehte per demo:

- Spark punon me micro-batches cdo 10 sekonda;
- `spark.sql.shuffle.partitions=2`;
- checkpointing perdoret per tolerancen ndaj nderprerjeve.

### Si ta shpjegosh kete pjese

Thuaj:

> Spark Streaming lexon eventet e ardhura nga Kafka, i pastron, i grupon me kohe dhe pastaj i ruan ne Cassandra. Ne te njejten kohe nxjerr edhe metrika, parashikime dhe alarme.

## 7. Ruajtja e te Dhenave ne Cassandra

Cassandra eshte baza kryesore per ruajtjen e te dhenave IoT. Skema gjendet ne `config/cassandra/init.cql`.

### Konfigurimi

- keyspace: `smart_parking`
- replication: `SimpleStrategy`
- replication factor: `1`

Kjo eshte e pershtatshme per ambient lokal dhe demo. Per deployment real mund te rritet numri i replikeve.

### Pse Cassandra

Te dhenat IoT jane:

- te shpeshta;
- te shkruara shume;
- te lexuara shpesh sipas parkingut, vendit ose kohes.

Prandaj Cassandra eshte zgjedhje e mire sepse eshte query-oriented dhe e shpejte per lexim me partition keys te sakta.

### Tabelat kryesore

| Tabela | Cfare ruan |
| --- | --- |
| `sensor_metadata_by_id` | Metadata per sensorin, zonen, gateway dhe statusin |
| `sensor_events_by_spot` | Historikun e plote te eventeve per secilin vend |
| `current_spot_status` | Gjendjen me te fundit per cdo vend parkimi |
| `parking_summary_by_minute` | Permbledhjen e parkingut per minute |
| `sensor_window_metrics_by_minute` | Metrikat e dritareve te Spark Streaming |
| `ai_results_by_time` | Rezultatet e prediction, anomaly, classification dhe pricing |
| `alerts_by_time` | Alarmet e gjeneruara nga sistemi |

### Si jane menduar primary keys

- `sensor_events_by_spot` perdor `(parking_id, spot_id)` si partition key qe te lexohet shpejt historia e nje vendi te vetem.
- `current_spot_status` perdor `parking_id` si partition key qe te lexohet gjendja aktuale e te gjithe parkingut.
- `parking_summary_by_minute` dhe `sensor_window_metrics_by_minute` perdorin `bucket_date` per te ndare te dhenat sipas dites.
- `ai_results_by_time` dhe `alerts_by_time` organizohen sipas dites dhe kohes se gjenerimit.

### Si te shpjegohet ne raport

Thuaj:

> Cassandra nuk perdoret si databaze e pergjithshme, por si storage i optimizuar per qasje te shpejte ndaj te dhenave historike dhe gjendjes aktuale. Skema eshte projektuar sipas pyetjeve qe i ben dashboard-i.

### Komanda per inicializim

```powershell
python -m app.storage.migrations
```

## 8. Nderfaqja e Vizualizimit

Dashboard-i i vizualizimit gjendet ne:

```text
http://127.0.0.1:8000/dashboard
```

Faqja hyrese e lokacioneve gjendet ne:

```text
http://127.0.0.1:8000/
```

### Teknologjite e perdorura

- FastAPI per backend;
- Vue 3 per UI;
- HTML/CSS/JavaScript per paraqitjen;
- `fetch()` per marrjen e snapshot-it JSON;
- refresh automatik cdo 6 sekonda;
- fallback simulation kur Cassandra s'ka ende te dhena.

### Cfare paraqet dashboard-i

Dashboard-i ka keto pjese kryesore:

- metrike te pergjithshme: vende te lira, okupim, forecast, cmim;
- tabela hyrese dhe tabela cmimi;
- plan vizual i parkingut;
- pamje `Plan`, `Sensore`, `AI`;
- panel per zonat;
- panel per pipeline-in;
- panel per shendetin e sensoreve.

### Si e lexon dashboard-i te dhenen

`DashboardService` i ben keto hapa:

1. lexon gjendjen nga Cassandra;
2. nese nuk ka rreshta, perdor nje snapshot simulative;
3. nese Cassandra eshte e paarritshme, aktivizon fallback-in;
4. i kthen te dhenat ne format JSON per frontend-in.

Kjo eshte shume e rendesishme per mbrojtje sepse dashboard-i mbetet funksional edhe kur pipeline-i live eshte ende duke u nisur.

### Si ta shpjegosh kete pjese

Thuaj:

> Dashboard-i nuk eshte vetem nje faqe statike. Ai lexon te dhena live nga Cassandra dhe paraqet gjendjen e parkingut, zonat, sensoret, anomali dhe cmimin dinamik. Kur s'ka te dhena live, kalon ne fallback qe demo-ja te mos deshtoje.

## 9. Fotot qe duhen vendosur ne dokument

Kjo eshte pjesa me e rendesishme per dorzim. Fotot jane ndare ne dy grupe: fotot e pipeline-it dhe fotot e dashboard-it.

### 9.1 Fotot qe duhet t'i marresh gjate demostrimit teknik

| Figura | Cfare te fotografosh | Si ta shpjegosh poshte fotos |
| --- | --- | --- |
| Figura 1 | Nje diagram te arkitektures `sensor -> MQTT -> Kafka -> Spark -> Cassandra -> Dashboard` | "Kjo figure paraqet rrjedhen e plote te sistemit dhe lidhjen mes te gjitha shtresave." |
| Figura 2 | Terminalin ku po ekzekutohet `python -m app.simulator.run_simulator` | "Ketu shihen te dhena te gjeneruara nga simulatori i sensoreve per secilin vend parkimi." |
| Figura 3 | Komanden `python -m scripts.init_kafka_topics` ose `kafka-topics --list` | "Kjo figure tregon qe topic-et e Kafka-s jane krijuar per raw events, processed events, alerts dhe AI." |
| Figura 4 | Terminalin e Spark Streaming ku shfaqet `Spark Streaming started` dhe batch writes | "Kjo figure tregon qe Spark po lexon nga Kafka, po i filtron eventet dhe po i ruan ne Cassandra." |
| Figura 5 | `cqlsh` ose nje DB GUI me query si `SELECT * FROM current_spot_status` | "Kjo figure tregon ruajtjen e te dhenave ne Cassandra dhe gjendjen aktuale te parkingut." |

### 9.2 Fotot e dashboard-it qe jane tashme ne repo

Keto foto jane te gatshme ne `docs/images/` dhe mund t'i fusesh direkt ne raport.

#### Figura 6. Dashboard overview

![Dashboard overview](images/dashboard-overview.PNG)

**Si ta shpjegosh:**
Pamja kryesore e dashboard-it. Tregon vendet e lira, okupimin, parashikimin per 30 minuta, cmimin dinamik dhe statusin e pergjithshem te sistemit.

#### Figura 7. Plan parkingu

![Dashboard plan](images/dashboard-plan.PNG)

**Si ta shpjegosh:**
Kjo figure paraqet planin vizual te parkingut me vendet e zena dhe te lira, te ndara ne Zona A dhe Zona B.

#### Figura 8. Pamja e sensoreve

![Dashboard sensors](images/dashboard-sensors.PNG)

**Si ta shpjegosh:**
Ketu shihen vlerat e sensorit per secilin vend: distanca, bateria dhe forca e sinjalit. Kjo tregon anen e telemetrise se sistemit.

#### Figura 9. Pamja AI

![Dashboard AI](images/dashboard-ai.PNG)

**Si ta shpjegosh:**
Kjo pamje tregon klasifikimin, anomaly detection dhe perqindjen e scores per secilin vend. Ketu shihen edhe vendet me `sensor_fault` ose `low_battery`.

#### Figura 10. Skenari maintenance

![Dashboard maintenance scenario](images/dashboard-maintance-scenario.PNG)

**Si ta shpjegosh:**
Ky eshte skenari me i mire per demo sepse shfaq qellimisht defekte si bateri te ulet dhe sinjal te dobet, pra anomali qe profesori mund t'i vereje menjehere.

### 9.3 Fotot shtese qe rekomandohen

Nese deshiron ta besh dokumentin me te forte, shto edhe kete foto:

- screenshot i faqes hyrese `http://127.0.0.1:8000/` qe tregon lokacionet e parkimit dhe hyrjen ne dashboard;
- screenshot i Swagger UI ne `http://127.0.0.1:8000/docs` per te treguar endpoint-et e API-se.

### 9.4 Renditja e rekomanduar e fotove ne raport

1. Figura 1 - arkitektura e sistemit.
2. Figura 2 - simulatori.
3. Figura 3 - Kafka topics.
4. Figura 4 - Spark Streaming.
5. Figura 5 - Cassandra.
6. Figura 6 - dashboard overview.
7. Figura 7 - plan parkingu.
8. Figura 8 - sensoret.
9. Figura 9 - AI.
10. Figura 10 - maintenance.

Kjo renditje e tregon profesorit qe raporti ndjek sakte pipeline-in teknik dhe pastaj pjesen e vizualizimit.

## 10. Sfidat e hasura

Gjate ndertimit te sistemit jane hasur disa sfida tipike per nje projekt IoT real-time:

- sinkronizimi i sherbimeve Docker;
- dizenjimi i skemes se Cassandra sipas pyetjeve qe behet nga dashboard-i;
- menaxhimi i rrjedhes se te dhenave kur nje sherbim ende nuk ka nisur;
- validimi i payload-eve qe vijne nga simulatori;
- ndarja e qarte mes te dhenave raw, processed dhe alerts;
- mbajtja e dashboard-it funksional edhe pa te dhena live.

### Si u zgjidhen

- u perdor MQTT gateway per validim dhe normalizim;
- u perdor Kafka si shtrese transmetimi;
- u perdor Spark Structured Streaming me schema dhe checkpointing;
- u perdor Cassandra me tabela query-oriented;
- u shtua fallback simulation qe demo-ja te mos bllokohet.

## 11. Mesimet e nxjerra

Nga ky projekt u kuptua qarte qe:

- ndarja e shtresave e ben sistemin me te lehte per mirembajtje;
- Kafka eshte shume i dobishem kur prodhuesi dhe konsumatori nuk duhet te jene te lidhur direkt;
- Spark Streaming eshte i pershtatshem per validim, agregim dhe perpunim ne kohe reale;
- Cassandra funksionon mire kur modelimi behet sipas query-ve dhe jo vetem sipas normalizimit klasik;
- nje dashboard i mire duhet te jete i qarte, i shpejte dhe i qendrueshem edhe kur te dhenat live mungojne.

## 12. Perfundime dhe rekomandime

Projekti e realizon me sukses nje sistem Smart Parking IoT duke bashkuar:

- mbledhjen e te dhenave nga sensore te simuluar;
- transmetimin permes MQTT dhe Kafka;
- perpunimin ne kohe reale me Spark Streaming;
- ruajtjen ne Apache Cassandra;
- vizualizimin ne nje dashboard web interaktiv.

### Arritjet kryesore

- sistemi ka pipeline te plote dhe te qarte;
- dashboard-i jep pamje vizuale te parkimit ne kohe reale;
- Cassandra ruan te dhenat historike dhe gjendjen aktuale;
- AI shton parashikim, klasifikim dhe alarme;
- demo-ja mund te ekzekutohet lokalisht pa sensor fizik.

### Rekomandime per permiresim te metejshem

- integrim me sensore fizike reale;
- ruajtje e te dhenave ne cloud;
- autentikim per dashboard-in dhe API-ne;
- njoftime me email ose Telegram kur krijohen alarme;
- shtim i me shume parkingjeve dhe analizave krahasuese;
- charts te avancuara per historikun e okupimit dhe cmimit.

### Fjalia perfundimtare per dorzim

> Ky projekt demonstron nje zgjidhje te plote IoT per Smart Parking, ku te dhenat mblidhen, transmetohen, perpunohen, ruhen dhe vizualizohen ne kohe reale, duke permbushur kerkesat kryesore te lendes dhe te projektit final.
