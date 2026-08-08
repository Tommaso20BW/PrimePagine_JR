<div align="center">

# 📰☀️ PrimePagine JR

**Bot Telegram che pubblica ogni giorno le prime pagine dei tre quotidiani sportivi italiani.**

[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://github.com/Tommaso20BW/PrimePagine_JR/actions/workflows/start.yml/badge.svg)](https://github.com/Tommaso20BW/PrimePagine_JR/actions/workflows/start.yml)

</div>

## Panoramica

PrimePagine JR raccoglie in un solo album Telegram le copertine di:

1. Tuttosport;
2. La Gazzetta dello Sport;
3. Corriere dello Sport.

Le immagini non vengono scaricate né salvate nel repository: Telegram le recupera direttamente dagli URL pubblici dei rispettivi CDN.

## Come funziona

```text
GitHub Actions o esecuzione locale
                ↓
              bot.py
        ┌───────┼────────┐
        ↓       ↓        ↓
   Tuttosport Gazzetta Corriere
        └───────┼────────┘
                ↓
      Telegram sendMediaGroup
```

Ogni esecuzione:

1. controlla l'orario in `Europe/Rome`;
2. se parte nei 15 minuti precedenti le **07:00**, attende l'orario esatto;
3. aggiunge agli URL un parametro anti-cache composto da data, ora e un numero casuale;
4. costruisce un album con `sendMediaGroup`;
5. inserisce sulla prima immagine la data e la firma `@Juventus_Reborn`;
6. invia le tre copertine nell'ordine indicato sopra.

Se il processo parte più di 15 minuti prima, dopo le 07:00 o in ritardo, procede immediatamente.

## Sorgenti

| Quotidiano | Host |
| --- | --- |
| Tuttosport | `cdn.tuttosport.com` |
| La Gazzetta dello Sport | `images2.gazzettaobjects.it` |
| Corriere dello Sport | `cdn.corrieredellosport.it` |

Gli URL sono costanti definite in `bot.py`. Se un quotidiano cambia il percorso della copertina, occorre aggiornare il relativo valore.

## Struttura

```text
PrimePagine_JR/
├── bot.py
├── requirements.txt
└── .github/workflows/
    └── start.yml
```

## Requisiti

- Python 3.14, come nel workflow GitHub Actions;
- accesso ai tre CDN e alla Telegram Bot API.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configurazione

Configura in **Settings → Secrets and variables → Actions**:

| Secret | Uso |
| --- | --- |
| `TELEGRAM_TOKEN` | Token del bot Telegram |
| `TELEGRAM_CHAT_ID` | Chat o canale di destinazione |

Non servono chiavi API per i quotidiani.

## Avvio locale

### Linux e macOS

```bash
export TELEGRAM_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python bot.py
```

### PowerShell

```powershell
$env:TELEGRAM_TOKEN = "..."
$env:TELEGRAM_CHAT_ID = "..."
python bot.py
```

Per cambiare l'orario modifica `ORA_INVIO` in `bot.py`.

## GitHub Actions

Il workflow `.github/workflows/start.yml`:

- è avviabile manualmente con `workflow_dispatch`;
- usa Python 3.14;
- installa Requests e `tzdata`;
- ha un timeout di 10 minuti;
- annulla un run precedente dello stesso gruppo se ne parte uno nuovo;
- usa permessi di sola lettura per il contenuto del repository;
- elimina i propri run completati dalla cronologia.

Nel repository non è presente uno `schedule`. Per una pubblicazione quotidiana occorre avviare il workflow tramite un servizio esterno o aggiungere una pianificazione.

## Limiti noti

- I percorsi dei CDN non sono API stabili e possono cambiare.
- Se Telegram non riesce a scaricare anche una sola immagine, l'intero album può essere rifiutato.
- La richiesta `sendMediaGroup` non imposta un timeout.
- Il codice non valida esplicitamente i secret prima di costruire la richiesta.
- Errori HTTP o di rete vengono stampati nei log, ma non forzano attualmente il fallimento del processo.

---

Progetto amatoriale, non affiliato con Juventus Football Club, Telegram o i quotidiani citati.
