import os
import requests
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Orario esatto (ora italiana) in cui il messaggio deve partire.
# Il workflow puo' avviarsi qualche minuto prima (buffer anti-ritardo GitHub Actions):
# lo script aspetta comunque fino a questo orario preciso prima di inviare.
ORA_INVIO = (7, 0)  # (ore, minuti) - modifica qui se vuoi cambiare orario
FUSO_ORARIO = ZoneInfo("Europe/Rome")


def attendi_orario_preciso(ora, minuto, fuso, margine_massimo_minuti=15):
    """Aspetta fino a ora:minuto (ora italiana). Se il workflow parte in ritardo
    oltre il margine massimo, invia subito senza aspettare oltre."""
    ora_corrente = datetime.now(fuso)
    target = ora_corrente.replace(hour=ora, minute=minuto, second=0, microsecond=0)

    secondi_attesa = (target - ora_corrente).total_seconds()

    if secondi_attesa <= 0:
        # Siamo gia' arrivati o superato l'orario target: invia subito.
        return

    if secondi_attesa > margine_massimo_minuti * 60:
        # Il job e' partito troppo presto rispetto al previsto: non ha senso
        # aspettare cosi' a lungo, si invia subito per evitare blocchi assurdi.
        print(f"Attesa di {secondi_attesa/60:.1f} minuti fuori dal margine, invio subito.")
        return

    print(f"Attendo {secondi_attesa:.0f} secondi per raggiungere le {ora:02d}:{minuto:02d} ora italiana...")
    time.sleep(secondi_attesa)

# Configurazione (Prende i dati dalle variabili d'ambiente)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Lista stabile: Tuttosport in testa
LINK_TUTTOSPORT = "https://cdn.tuttosport.com/next/img/edizioni/ts/prima-pagina-naz-810x1189.jpg"
LINK_GAZZETTA = "https://images2.gazzettaobjects.it/images/primepagine/gazzettafc_nazionale_web-Big.jpg"
LINK_CORRIERE = "https://cdn.corrieredellosport.it/next/img/edizioni/cds/prima-pagina-naz-810x1189.jpg"

def invia_album():
    url_telegram = f"https://api.telegram.org/bot{TOKEN}/sendMediaGroup"
    
    # Genera la data di oggi
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    
    # Genera il codice unico anti-cache
    anti_cache = datetime.now().strftime("%Y%m%d%H%M") + str(random.randint(10, 99))
    
    PRIME_PAGINE = [
        f"{LINK_TUTTOSPORT}?v={anti_cache}",
        f"{LINK_GAZZETTA}?v={anti_cache}",
        f"{LINK_CORRIERE}?v={anti_cache}"
    ]
    
    # Costruzione della didascalia con emoji standard (senza tag tg-emoji)
    didascalia = (
        f'📰☀️ '
        f'<b>PRIME PAGINE | {data_oggi}</b>\n\n'
        f'👉 @Juventus_Reborn'
    )

    media = []
    for i, url in enumerate(PRIME_PAGINE):
        oggetto_foto = {
            "type": "photo",
            "media": url
        }
        if i == 0:
            oggetto_foto["caption"] = didascalia
            oggetto_foto["parse_mode"] = "HTML"
            
        media.append(oggetto_foto)

    payload = {
        "chat_id": CHAT_ID,
        "media": media
    }
    
    try:
        risposta = requests.post(url_telegram, json=payload)
        
        if risposta.status_code == 200:
            print("Album inviato con la struttura esatta del JSON!")
        else:
            print(f"Errore restituito da Telegram: {risposta.text}")
            
    except Exception as e:
        print(f"Errore di connessione: {e}")

if __name__ == "__main__":
    attendi_orario_preciso(ORA_INVIO[0], ORA_INVIO[1], FUSO_ORARIO)
    invia_album()
