import os
import requests
import random
from datetime import datetime

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
    
    # Nuova didascalia speculare al tuo JSON (Giornale + Sole + Tutto il titolo in Grassetto)
    didascalia = (
        f'<tg-emoji emoji-id="5433982607035474385">📰</tg-emoji>'
        f'<tg-emoji emoji-id="5469947168523558652">☀️</tg-emoji> '
        f'<b>PRIME PAGINE | {data_oggi}</b>\n\n'
        f'<tg-emoji emoji-id="5985659276327132147">👉</tg-emoji> <u>@Juventus_Reborn</u>'
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
            print("Album aggiornato con nuova grafica inviato con successo!")
        else:
            print(f"Errore restituito da Telegram: {risposta.text}")
            
    except Exception as e:
        print(f"Errore di connessione: {e}")

if __name__ == "__main__":
    invia_album()
