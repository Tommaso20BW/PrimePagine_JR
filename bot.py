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

ORA_INIZIO = (7, 0)   # Mai pubblicare prima delle 07:00
ORA_LIMITE = (8, 0)   # Alle 08:00 invia quelle nuove trovate
INTERVALLO_CONTROLLI = 5 * 60  # 5 minuti

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

def carica_stato():
    stato = {
        "hashes": {chiave: None for chiave in GIORNALI},
        "ultima_data_invio": None,
    }

    if not os.path.exists(STATE_FILE):
        return stato

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            salvato = json.load(file)

        hashes_salvati = salvato.get("hashes", {})
        for chiave in GIORNALI:
            stato["hashes"][chiave] = hashes_salvati.get(chiave)

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
# ORARI
# ============================================================

def adesso_italia():
    return datetime.now(FUSO_ORARIO)


def attendi_fino_alle_7():
    """Non permette mai una pubblicazione prima delle 07:00."""
    adesso = adesso_italia()
    target = adesso.replace(
        hour=ORA_INIZIO[0],
        minute=ORA_INIZIO[1],
        second=0,
        microsecond=0,
    )

    secondi = (target - adesso).total_seconds()

    if secondi > 0:
        print(
            f"Sono le {adesso:%H:%M:%S}. "
            f"Attendo le {target:%H:%M} prima del primo controllo."
        )
        time.sleep(secondi)


def limite_di_oggi():
    adesso = adesso_italia()
    return adesso.replace(
        hour=ORA_LIMITE[0],
        minute=ORA_LIMITE[1],
        second=0,
        microsecond=0,
    )


# ============================================================
# DOWNLOAD
# ============================================================

def scarica_giornale(chiave, configurazione):
    """
    Scarica l'immagine e calcola SHA-256 sui byte reali della foto.
    Il parametro ?v= cambia solo per evitare la cache e NON entra nell'hash.
    """
    anti_cache = str(int(time.time() * 1000))
    url = f"{configurazione['url']}?v={anti_cache}"

    try:
        risposta = requests.get(url, headers=HEADERS, timeout=30)
        risposta.raise_for_status()

        contenuto = risposta.content
        if not contenuto:
            raise ValueError("risposta vuota")

        content_type = risposta.headers.get("Content-Type", "").lower()
        if content_type and "image" not in content_type:
            raise ValueError(f"contenuto non immagine: {content_type}")

        return {
            "chiave": chiave,
            "nome": configurazione["nome"],
            "filename": configurazione["filename"],
            "contenuto": contenuto,
            "hash": calcola_sha256(contenuto),
        }

    except Exception as errore:
        print(f"{configurazione['nome']}: errore download -> {errore}")
        return None


def controlla_prime_pagine(stato, trovate):
    print(f"\nControllo delle {adesso_italia():%H:%M:%S}...")

    for chiave, configurazione in GIORNALI.items():
        risultato = scarica_giornale(chiave, configurazione)

        if risultato is None:
            continue

        hash_precedente = stato["hashes"].get(chiave)
        hash_attuale = risultato["hash"]

        if hash_attuale == hash_precedente:
            print(
                f"{configurazione['nome']}: VECCHIA "
                f"(hash {hash_attuale[:12]}...)"
            )
            continue

        # Nuova rispetto all'ultima copertina effettivamente pubblicata.
        # Se era già stata trovata in un controllo precedente, la aggiorniamo
        # con l'ultima versione ricevuta.
        trovate[chiave] = risultato
        print(
            f"{configurazione['nome']}: NUOVA "
            f"(hash {hash_attuale[:12]}...)"
        )

    print(f"Nuove trovate finora: {len(trovate)}/3")
    return trovate


# ============================================================
# TELEGRAM
# ============================================================

def crea_didascalia():
    data_oggi = adesso_italia().strftime("%d/%m/%Y")
    return (
        f"📰☀️ <b>PRIME PAGINE | {data_oggi}</b>\n\n"
        f"👉 @Juventus_Reborn"
    )


def ordina_trovate(trovate):
    return [trovate[chiave] for chiave in GIORNALI if chiave in trovate]


def invia_foto_singola(elemento, didascalia):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    files = {
        "photo": (
            elemento["filename"],
            elemento["contenuto"],
            "image/jpeg",
        )
    }
    data = {
        "chat_id": CHAT_ID,
        "caption": didascalia,
        "parse_mode": "HTML",
    }

    risposta = requests.post(url, data=data, files=files, timeout=60)
    risposta.raise_for_status()


def invia_album(elementi, didascalia):
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
            oggetto["caption"] = didascalia
            oggetto["parse_mode"] = "HTML"

        media.append(oggetto)

        files[nome_attach] = (
            elemento["filename"],
            elemento["contenuto"],
            "image/jpeg",
        )

    data = {
        "chat_id": CHAT_ID,
        "media": json.dumps(media, ensure_ascii=False),
    }

    risposta = requests.post(url, data=data, files=files, timeout=90)
    risposta.raise_for_status()


def invia_trovate(trovate, stato):
    elementi = ordina_trovate(trovate)

    if not elementi:
        print("Nessuna prima pagina nuova da inviare.")
        return False

    if not TOKEN or not CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti."
        )

    didascalia = crea_didascalia()

    print(f"Invio di {len(elementi)} prima/e pagina/e...")

    if len(elementi) == 1:
        invia_foto_singola(elementi[0], didascalia)
    else:
        invia_album(elementi, didascalia)

    # Aggiorna gli hash SOLO dopo un invio Telegram riuscito.
    for elemento in elementi:
        stato["hashes"][elemento["chiave"]] = elemento["hash"]

    stato["ultima_data_invio"] = adesso_italia().strftime("%Y-%m-%d")
    salva_stato(stato)

    print("Invio completato. state.json aggiornato.")
    return True


# ============================================================
# LOGICA PRINCIPALE
# ============================================================

def main():
    stato = carica_stato()
    trovate = {}

    # 1) Mai prima delle 07:00.
    attendi_fino_alle_7()

    limite = limite_di_oggi()

    # 2) Primo controllo delle 07:00 (o appena parte, se è già dopo le 07:00).
    trovate = controlla_prime_pagine(stato, trovate)

    # NUOVA REGOLA:
    # se al PRIMO controllo non troviamo nemmeno una prima pagina nuova,
    # il bot termina immediatamente e non continua fino alle 08:00.
    if len(trovate) == 0:
        print(
            "Al primo controllo non è stata trovata nessuna prima pagina nuova. "
            "Termino senza inviare nulla."
        )
        return

    # Se sono già tutte e 3 nuove, invio subito.
    if len(trovate) == len(GIORNALI):
        print("Tutte e 3 nuove: invio immediato.")
        invia_trovate(trovate, stato)
        return

    # Se il workflow è partito tardi ed è già >= 08:00,
    # invia subito quelle trovate al primo controllo.
    if adesso_italia() >= limite:
        print("Orario limite già raggiunto: invio quelle nuove trovate.")
        invia_trovate(trovate, stato)
        return

    # 3) Se alle 07:00 ne abbiamo trovata almeno 1 ma meno di 3,
    # ricontrolliamo ogni 5 minuti fino alle 08:00.
    while True:
        adesso = adesso_italia()
        secondi_mancanti = (limite - adesso).total_seconds()

        if secondi_mancanti <= 0:
            print("Sono le 08:00: invio le prime pagine nuove trovate.")
            invia_trovate(trovate, stato)
            return

        attesa = min(INTERVALLO_CONTROLLI, secondi_mancanti)
        prossimo = datetime.fromtimestamp(adesso.timestamp() + attesa, FUSO_ORARIO)

        print(
            f"Nuove trovate: {len(trovate)}/3. "
            f"Prossimo controllo alle {prossimo:%H:%M:%S}."
        )
        time.sleep(attesa)

        trovate = controlla_prime_pagine(stato, trovate)

        if len(trovate) == len(GIORNALI):
            print("Ora sono tutte e 3 nuove: invio immediato.")
            invia_trovate(trovate, stato)
            return

        if adesso_italia() >= limite:
            print("Raggiunte le 08:00: invio quelle nuove trovate.")
            invia_trovate(trovate, stato)
            return


if __name__ == "__main__":
    main()
