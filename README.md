<div align="center">

# 📰☀️ PrimePagine JR

**Bot Telegram che pubblica in automatico le prime pagine dei principali quotidiani sportivi italiani.**

Semplice, leggero, senza dipendenze esterne né API key: gira interamente su **GitHub Actions**.

`Python 3.12` · `requests` · `Telegram Bot API` · `GitHub Actions`

</div>

-----

## Indice

- [Cos’è](#cosè)
- [Come funziona](#come-funziona)
- [Funzionalità](#funzionalità)
- [Sorgenti immagini](#sorgenti-immagini)
- [Formato del messaggio](#formato-del-messaggio)
- [Struttura del repository](#struttura-del-repository)
- [Configurazione](#configurazione)
- [Avvio](#avvio)
- [Stack tecnico](#stack-tecnico)

-----

## Cos’è

PrimePagine JR recupera ogni giorno le immagini delle prime pagine di Tuttosport, Gazzetta dello Sport e Corriere dello Sport direttamente dai rispettivi CDN ufficiali, le raggruppa in un **album fotografico** e le invia al canale Telegram **@Juventus_Reborn** con la data del giorno.

-----

## Come funziona

```
                ┌──────────────────────┐
                │   GitHub Actions      │  ← avvio manuale o cron giornaliero
                │       start.yml       │
                └──────────┬───────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │                bot.py                 │
        │  1. costruisce gli URL anti-cache     │
        │  2. scarica le 3 prime pagine         │
        │  3. invia l'album con didascalia      │
        └───────────────┬──────────┬─────────────┘
                        │          │
                        ▼          ▼
                  ┌─────────────┐  ┌──────────┐
                  │     CDN     │  │ Telegram │
                  │ quotidiani  │  │ (output) │
                  │ TS·GdS·CdS  │  │          │
                  └─────────────┘  └──────────┘
```

Lo script è volutamente minimale: meno di 60 righe di Python. Costruisce per ogni quotidiano un URL con un parametro anti-cache, scarica le tre immagini dai CDN pubblici e le inoltra a Telegram come unico album tramite `sendMediaGroup`, con la didascalia sulla prima foto.

-----

## Funzionalità

- **Tre quotidiani in un colpo solo** — Tuttosport, Gazzetta dello Sport e Corriere dello Sport inviati come album unico.
- **Anti-cache automatico** — ogni URL viene reso unico aggiungendo un parametro `?v=` basato su data/ora e numero casuale, per forzare il download dell’immagine più recente invece di quella cachata.
- **Album Telegram** — le tre prime pagine vengono inviate come `sendMediaGroup` con la didascalia sulla prima immagine.
- **Nessuna API key richiesta** — le immagini vengono scaricate direttamente dai CDN pubblici dei quotidiani.
- **Script minimalista** — meno di 60 righe di Python, zero dipendenze oltre a `requests`.

-----

## Sorgenti immagini

|Quotidiano          |CDN                         |
|--------------------|----------------------------|
|Tuttosport          |`cdn.tuttosport.com`        |
|Gazzetta dello Sport|`images2.gazzettaobjects.it`|
|Corriere dello Sport|`cdn.corrieredellosport.it` |

-----

## Formato del messaggio

```
📰☀️ PRIME PAGINE | GG/MM/AAAA

👉 @Juventus_Reborn
```

*(didascalia sulla prima foto dell’album)*

-----

## Struttura del repository

```
PrimePagine_JR/
├── bot.py                    # Script principale
├── requirements.txt          # Dipendenze Python (solo requests)
└── .github/workflows/
    └── start.yml             # Workflow GitHub Actions
```

-----

## Configurazione

In **Settings → Secrets and variables → Actions** aggiungi:

|Secret            |Descrizione                        |
|------------------|-----------------------------------|
|`TELEGRAM_TOKEN`  |Token del bot Telegram.            |
|`TELEGRAM_CHAT_ID`|Chat ID del canale di destinazione.|

-----

## Avvio

1. Fai il **fork** del repository.
1. Configura i due secret elencati sopra.
1. Avvia il workflow da `Actions → Invia Prime Pagine Giornaliere → Run workflow`.

> Per automatizzare l’invio ogni mattina, aggiungi uno schedule cron al workflow:
> 
> ```yaml
> on:
>   schedule:
>     - cron: '30 5 * * *'   # ogni giorno alle 05:30 UTC (07:30 ora italiana)
>   workflow_dispatch:
> ```

-----

## Stack tecnico

`Python 3.12` · `requests` · `GitHub Actions`

-----

<div align="center">

*Progetto amatoriale. Non affiliato con la Juventus FC, Telegram o i quotidiani citati.*

</div>