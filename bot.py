import os
import requests
from datetime import datetime

# Configurazione (Prende i dati dalle variabili d'ambiente)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Lista con Tuttosport in testa
PRIME_PAGINE = [
    "https://cdn.tuttosport.com/next/img/edizioni/ts/prima-pagina-naz-810x1189.jpg",
    "https://images2.gazzettaobjects.it/images/primepagine/gazzettafc_nazionale_web-Big.jpg",
    "https://cdn.corrieredellosport.it/next/img/edizioni/cds/prima-pagina-naz-810x1189.jpg"
]

def invia_album():
    url_telegram = f"https://api.telegram.org/bot{TOKEN}/sendMediaGroup"
    
    # Genera la data di oggi
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    
    # Didascalia speculare al tuo ultimo JSON (senza calendario e con spazi corretti)
    didascalia = (
        f'<tg-emoji id="5433982607035474385">📰</tg-emoji> '
        f'<b>PRIME PAGINE | {data_oggi}</b>\n\n'
        f'<tg-emoji id="5985659276327132147">👉</tg-emoji> <u>@Juventus_Reborn</u>'
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
            print("Album inviato con successo!")
        else:
            print(f"Errore restituito da Telegram: {risposta.text}")
            
    except Exception as e:
        print(f"Errore di connessione: {e}")

if __name__ == "__main__":
    invia_album()
