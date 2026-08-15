import hashlib
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


# ============================================================
# CONFIGURAZIONE
# ============================================================

FUSO_ORARIO = ZoneInfo("Europe/Rome")
ORA_INVIO = (7, 0)

TENTATIVI_DOWNLOAD = 3
PAUSA_TENTATIVI = 3

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "state.json"

GIORNALI = {
    "tuttosport": {
        "nome": "Tuttosport",
        "url": "https://cdn.tuttosport.com/next/img/edizioni/ts/prima-pagina-naz-810x1189.jpg",
        "filename": "tuttosport.jpg",
    },
    "gazzetta": {
        "nome": "La Gazzetta dello Sport",
        "url": "https://images2.gazzettaobjects.it/images/primepagine/gazzettafc_nazionale_web-Big.jpg",
        "filename": "gazzetta.jpg",
    },
    "corriere": {
        "nome": "Corriere dello Sport",
        "url": "https://cdn.corrieredellosport.it/next/img/edizioni/cds/prima-pagina-naz-810x1189.jpg",
        "filename": "corriere.jpg",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# ============================================================
# STATO / HASH
# ============================================================

def stato_vuoto():
    return {
        "hashes": {chiave: None for chiave in GIORNALI},
        "ultima_data_controllo": None,
        "ultima_data_invio": None,
    }


def carica_stato():
    stato = stato_vuoto()

    if not os.path.exists(STATE_FILE):
        return stato

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            salvato = json.load(file)

        hashes_salvati = salvato.get("hashes", {})

        for chiave in GIORNALI:
            stato["hashes"][chiave] = hashes_salvati.get(chiave)

        stato["ultima_data_controllo"] = salvato.get("ultima_data_controllo")
        stato["ultima_data_invio"] = salvato.get("ultima_data_invio")

    except Exception as errore:
        print(f"Impossibile leggere {STATE_FILE}: {errore}")
        print("Uso uno stato vuoto.")

    return stato


def salva_stato(stato):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(stato, file, ensure_ascii=False, indent=2)
        file.write("\n")


def calcola_sha256(contenuto):
    return hashlib.sha256(contenuto).hexdigest()


# ============================================================
# ORARIO
# ============================================================

def adesso_italia():
    return datetime.now(FUSO_ORARIO)


def attendi_fino_alle_7():
    adesso = adesso_italia()

    target = adesso.replace(
        hour=ORA_INVIO[0],
        minute=ORA_INVIO[1],
        second=0,
        microsecond=0,
    )

    secondi = (target - adesso).total_seconds()

    if secondi > 0:
        print(
            f"Sono le {adesso:%H:%M:%S}. "
            f"Attendo le {target:%H:%M} prima del controllo."
        )
        time.sleep(secondi)


# ============================================================
# DOWNLOAD
# ============================================================

def scarica_giornale(chiave, configurazione):
    ultimo_errore = None

    for tentativo in range(1, TENTATIVI_DOWNLOAD + 1):
        anti_cache = str(int(time.time() * 1000))
        url = f"{configurazione['url']}?v={anti_cache}"

        try:
            print(
                f"{configurazione['nome']}: download "
                f"tentativo {tentativo}/{TENTATIVI_DOWNLOAD}..."
            )

            risposta = requests.get(
                url,
                headers=HEADERS,
                timeout=30,
            )

            risposta.raise_for_status()

            contenuto = risposta.content

            if not contenuto:
                raise ValueError("risposta vuota")

            content_type = risposta.headers.get(
                "Content-Type",
                "",
            ).lower()

            if content_type and "image" not in content_type:
                raise ValueError(
                    f"contenuto non immagine: {content_type}"
                )

            if tentativo > 1:
                print(
                    f"{configurazione['nome']}: download riuscito "
                    f"al tentativo {tentativo}."
                )

            return {
                "chiave": chiave,
                "nome": configurazione["nome"],
                "filename": configurazione["filename"],
                "contenuto": contenuto,
                "hash": calcola_sha256(contenuto),
            }

        except Exception as errore:
            ultimo_errore = errore

            print(
                f"{configurazione['nome']}: errore download "
                f"(tentativo {tentativo}/{TENTATIVI_DOWNLOAD}) -> {errore}"
            )

            if tentativo < TENTATIVI_DOWNLOAD:
                print(
                    f"{configurazione['nome']}: nuovo tentativo "
                    f"tra {PAUSA_TENTATIVI} secondi..."
                )

                time.sleep(PAUSA_TENTATIVI)

    print(
        f"{configurazione['nome']}: download fallito dopo "
        f"{TENTATIVI_DOWNLOAD} tentativi -> {ultimo_errore}"
    )

    return None


# ============================================================
# TELEGRAM
# ============================================================

def crea_didascalia():
    data_oggi = adesso_italia().strftime("%d/%m/%Y")

    return (
        f"📰☀️ <b>PRIME PAGINE | {data_oggi}</b>\n\n"
        f"👉 @Juventus_Reborn"
    )


def invia_album(elementi):
    if not TOKEN or not CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti."
        )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMediaGroup"

    media = []
    files = {}

    for indice, elemento in enumerate(elementi):
        nome_attach = f"foto{indice}"

        oggetto = {
            "type": "photo",
            "media": f"attach://{nome_attach}",
        }

        if indice == 0:
            oggetto["caption"] = crea_didascalia()
            oggetto["parse_mode"] = "HTML"

        media.append(oggetto)

        files[nome_attach] = (
            elemento["filename"],
            elemento["contenuto"],
            "image/jpeg",
        )

    data = {
        "chat_id": CHAT_ID,
        "media": json.dumps(
            media,
            ensure_ascii=False,
        ),
    }

    risposta = requests.post(
        url,
        data=data,
        files=files,
        timeout=90,
    )

    risposta.raise_for_status()


# ============================================================
# MAIN
# ============================================================

def main():
    stato = carica_stato()

    attendi_fino_alle_7()

    print(
        f"Controllo delle "
        f"{adesso_italia():%H:%M:%S}..."
    )

    risultati = []
    non_aggiornati = []

    for chiave, configurazione in GIORNALI.items():
        risultato = scarica_giornale(
            chiave,
            configurazione,
        )

        if risultato is None:
            print(
                "Una o più prime pagine non sono verificabili. "
                "Nessun invio effettuato."
            )
            return

        hash_precedente = stato["hashes"].get(chiave)
        hash_attuale = risultato["hash"]

        if (
            hash_precedente is not None
            and hash_attuale == hash_precedente
        ):
            print(
                f"{configurazione['nome']}: NON AGGIORNATA "
                f"(hash {hash_attuale[:12]}...)"
            )

            non_aggiornati.append(chiave)

        else:
            print(
                f"{configurazione['nome']}: NUOVA "
                f"(hash {hash_attuale[:12]}...)"
            )

        risultati.append(risultato)

    for risultato in risultati:
        stato["hashes"][risultato["chiave"]] = risultato["hash"]

    stato["ultima_data_controllo"] = (
        adesso_italia().strftime("%Y-%m-%d")
    )

    salva_stato(stato)

    if non_aggiornati:
        print(
            "Una o più prime pagine non risultano aggiornate. "
            "Nessun invio effettuato."
        )
        return

    print(
        "Tutte e 3 le prime pagine risultano aggiornate: "
        "invio album."
    )

    invia_album(risultati)

    stato["ultima_data_invio"] = (
        adesso_italia().strftime("%Y-%m-%d")
    )

    salva_stato(stato)

    print("Album inviato correttamente.")


if __name__ == "__main__":
    main()
