# 📰☀️ PrimePagine JR

Bot Telegram che pubblica in un unico album le prime pagine di:

- Tuttosport;
- La Gazzetta dello Sport;
- Corriere dello Sport.

Le immagini vengono referenziate direttamente dai CDN dei quotidiani; il bot non le salva nel repository.

## Come funziona

1. Se il processo parte nei 15 minuti precedenti le **07:00 (Europe/Rome)**, attende l’orario esatto. Se parte prima, dopo o con un ritardo maggiore, procede subito.
2. Costruisce i tre URL delle copertine aggiungendo un parametro anti-cache basato su data, ora e un numero casuale.
3. Prepara un album Telegram con `sendMediaGroup`.
4. Inserisce sulla prima foto una didascalia HTML con la data corrente e `@Juventus_Reborn`.
5. Invia le immagini nell’ordine Tuttosport, Gazzetta, Corriere.

```text
GitHub Actions / esecuzione locale
                │
                ▼
              bot.py
        ┌───────┼────────┐
        ▼       ▼        ▼
   Tuttosport Gazzetta Corriere CDN
        └───────┼────────┘
                ▼
       Telegram sendMediaGroup
```

## Sorgenti

| Quotidiano | Host |
|---|---|
| Tuttosport | `cdn.tuttosport.com` |
| La Gazzetta dello Sport | `images2.gazzettaobjects.it` |
| Corriere dello Sport | `cdn.corrieredellosport.it` |

Gli URL sono definiti come costanti in `bot.py` e possono essere aggiornati se i quotidiani cambiano percorso.

## GitHub Actions

Il workflow [`.github/workflows/start.yml`](.github/workflows/start.yml):

- è avviabile **solo manualmente** con `workflow_dispatch`;
- usa Python 3.12;
- installa `requests` da `requirements.txt`;
- richiede permessi repository in sola lettura;
- impedisce esecuzioni sovrapposte tramite un concurrency group;
- ha un timeout di 10 minuti.

Nel repository non è configurato uno schedule. Per la pubblicazione quotidiana occorre aggiungere un trigger cron o avviare il workflow tramite un servizio esterno.

## Configurazione

In **Settings → Secrets and variables → Actions** configura:

| Secret | Obbligatorio | Uso |
|---|---:|---|
| `TELEGRAM_TOKEN` | sì | Token del bot Telegram. |
| `TELEGRAM_CHAT_ID` | sì | Chat o canale di destinazione. |

Non servono chiavi API per i quotidiani.

## Avvio

### Da GitHub

Apri **Actions → Invia Prime Pagine Giornaliere → Run workflow**.

### In locale

```bash
python -m pip install -r requirements.txt
python bot.py
```

Prima dell’avvio esporta `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID`.

## Struttura

```text
PrimePagine_JR/
├── bot.py
├── requirements.txt
└── .github/workflows/
    └── start.yml
```

## Limiti noti

- La disponibilità delle copertine dipende da URL esterni non garantiti come API stabili.
- Telegram scarica le immagini dagli URL indicati: se un CDN non è raggiungibile, l’intero album può fallire.
- La richiesta di invio non imposta un timeout e gli errori vengono stampati nei log senza forzare sempre il fallimento del processo.
- Il codice non valida esplicitamente i secret prima di costruire la richiesta Telegram.

---

Progetto amatoriale, non affiliato con Juventus FC, Telegram o i quotidiani citati.
