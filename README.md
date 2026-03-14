# 🛒 Amazon Affiliate Link Optimizer - Telegram Bot

Un bot Telegram asincrono scritto in Python che riceve link di prodotti Amazon, ne estrae l'ASIN e restituisce un link pulito e ottimizzato con il tuo tag di affiliazione. Sviluppato per supportare la community di @nerdalquadrato.

## ✨ Funzionalità

* **Risoluzione Asincrona:** Risolve automaticamente e in modo asincrono (non bloccante) gli short link come `amzn.to` o `amzn.eu` utilizzando `httpx`.
* **Estrazione ASIN Precisa:** Utilizza le espressioni regolari (RegEx) per individuare il codice ASIN a 10 caratteri da qualsiasi tipologia di URL Amazon.
* **Validazione Geografica:** Verifica che il prodotto appartenga allo store italiano (`amazon.it`). Se il link è estero, avvisa l'utente.
* **Gestione Multi-Link:** Elabora fino a un massimo di 5 link contemporaneamente nello stesso messaggio per evitare sovraccarichi o spam.
* **Logging Integrato:** Stampa a terminale data, ora e stato di ogni richiesta in ingresso.

## 🛠️ Requisiti

* Python 3.8 o superiore.
* Un token API per il bot Telegram (ottenibile tramite [@BotFather](https://t.me/BotFather) su Telegram).
