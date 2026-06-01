# Perputhja me materialin e mesuar ne lende

U lexuan materialet e lendes nga:

- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (3).pdf`
- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (4).pdf`
- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (5).pdf`
- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (6).pdf`
- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (7).pdf`
- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (8).pdf`
- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (10).pdf`
- `c:\Users\perve\Desktop\0 Master\ai\ligjeratat\download. (11).pdf`

`download. (9).pdf` nuk u gjet ne disk gjate kontrollit. Ne te njejten dosje ekzistojne edhe materiale shtese `download. (1).pdf`, `download. (2).pdf`, `download. (12).pdf`, `download. (13).pdf`, `download. (14).pdf`, `download. (15).pdf`, `download. (16).pdf`, te cilat konfirmojne temat kryesore te lendes.

## Cfare u mesua dhe si perdoret ne projekt

| Materiali | Tema kryesore | Perdorimi ne projekt |
| --- | --- | --- |
| `download. (3).pdf` | Adversarial search, minimax, alpha-beta | Nuk perdoret ne pipeline sepse parkingu nuk eshte loje/adversarial problem |
| `download. (4).pdf` | Uncertainty, utilities, expectimax, expected utility | Cmimi dinamik trajtohet si rregull aplikativ/utility, jo si algoritëm i ri ML |
| `download. (5).pdf` | CSP, constraints, local search, hill climbing, genetic algorithms | Validimet e sensorit dhe kufizimet e payload-it shpjegohen si hard constraints |
| `download. (6).pdf` | Knowledge-based agents, knowledge representation, logic | Rregullat e alarmimit jane knowledge/rule-based |
| `download. (7).pdf` | Logic, inference, resolution, fuzzy logic | Alarmet dhe gjendjet e sensorit mbahen interpretable me rregulla te qarta |
| `download. (8).pdf` | Probability, conditional probability, Bayes rule | Arsyetimi probabilistik mbeshtet interpretimin e sensor readings dhe pasigurise |
| `download. (10).pdf` | Bayes nets, independence, conditional independence | Pjesa e AI nuk pretendon Bayes net sepse nuk eshte e nevojshme per prototipin |
| `download. (11).pdf` | Supervised learning, classification, regression, overfitting, cross-validation, reinforcement, k-means | Random Forest regression per forecast dhe Decision Tree classification per sensor status |
| `download. (13).pdf` | Naive Bayes, Laplace smoothing | Referohet si algoritëm i mesuar, por nuk perdoret sepse sensor features jane numerike dhe decision tree eshte me interpretable |
| `download. (14).pdf` | Neural networks, gradient descent, CNN/RNN | Nuk perdoret per te mos e renduar projektin dhe sepse profesori kerkoi permbajtje strikte/praktike |

## Vendime per maksimum pike

- Nuk perdoret deep learning, sepse do te ishte me i rende dhe jo i nevojshem per nje parking me 20 vende.
- Nuk perdoret Isolation Forest, sepse nuk u identifikua si teme e mesuar ne materialet e lexuara.
- Per anomaly/status perdoret `DecisionTreeClassifier`, sepse decision trees, entropy/information gain dhe classification jane pjese e lendes.
- Per parashikim okupimi perdoret `RandomForestRegressor`, sepse Random Forest dhe regression jane pjese e materialit.
- Per alarmim perdoren rregulla interpretable, te lidhura me knowledge-based agents dhe constraints.
- Per sistemin IoT ruhen strikt teknologjite e projektit: Kafka, Spark Streaming, Cassandra dhe web visualization.

