import re
import httpx
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- CONFIGURAZIONE ---
TOKEN_TELEGRAM = "8298053839:AAFa-T_6tgnHn2uyv4lekNApNM5whNqaayI" # TOKEN REVOCATO E SOSTITUITO
REFERRAL_TAG = "nerdalquadr0b-21"
# ----------------------

async def estrai_asin(url: str) -> str:
    """
    Valida il dominio, risolve gli short link in modo asincrono ed estrae l'ASIN a 10 caratteri.
    """
    try:
        parsed_url = urlparse(url)
        dominio = parsed_url.netloc.lower()
    except Exception:
        return None

    # Validazione rigorosa del dominio per evitare spoofing
    domini_validi_amazon = ["amazon.it", "www.amazon.it", "amazon.com", "www.amazon.com"]
    domini_short = ["amzn.to", "amzn.eu"]
    
    # Se il dominio non è tra quelli consentiti, interrompiamo l'elaborazione
    if not any(dominio.endswith(d) for d in domini_validi_amazon + domini_short):
        return None

    # Fase 1: Risoluzione short link in modo ASINCRONO non bloccante
    if any(dominio.endswith(d) for d in domini_short):
        try:
            async with httpx.AsyncClient() as client:
                # Seguiamo il redirect asincronamente
                response = await client.head(url, follow_redirects=True, timeout=5.0)
                url = str(response.url)
        except httpx.RequestError:
            return None

    # Fase 2: Estrazione ASIN tramite Regex (cattura ASIN alfanumerici e ISBN a 10 cifre)
    pattern = r"(?:/dp/|/gp/product/|/exec/obidos/ASIN/|/o/ASIN/|/as/|/p/)(?P<asin>[A-Z0-9]{10})"
    match = re.search(pattern, url, re.IGNORECASE)
    
    if match:
        return match.group("asin")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start inviando il messaggio di benvenuto."""
    messaggio_benvenuto = (
        f"🔗 Mandami il link <a href=\"https://amzn.to/4cZjQYd\">Amazon</a> desiderato!\n\n"
        f"In questo modo contribuirai gratuitamente a mantenere in vita <a href=\"https://nerdalquadrato.it\">i nostri progetti</a> di @nerdalquadrato!\n\n"
        f"<i>📌 In qualità di Affiliati Amazon, riceviamo un guadagno dagli acquisti idonei.</i>"
    )
    await update.message.reply_text(
        messaggio_benvenuto, 
        parse_mode=ParseMode.HTML, 
        disable_web_page_preview=True
    )

async def processa_messaggio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Intercetta i messaggi, esegue il parsing sicuro degli URL e restituisce il link pulito.
    """
    testo_utente = update.message.text
    
    # Identifica tutti gli URL presenti nel testo
    urls_trovati = re.findall(r'(https?://[^\s]+)', testo_utente)
    
    if not urls_trovati:
        return

    for url in urls_trovati:
        # Passiamo l'URL alla funzione asincrona di validazione ed estrazione
        asin = await estrai_asin(url)
        
        if asin:
            # Fase 3: Ricostruzione normalizzata del link
            link_pulito = f"https://www.amazon.it/dp/{asin}?tag={REFERRAL_TAG}"
            
            messaggio_finale = (
                f"Link ottimizzato:\n{link_pulito}\n\n"
                f"🔗 Manda un altro link quando vuoi, in questo modo contribuirai gratuitamente a mantenere in vita <a href=\"https://nerdalquadrato.it\">i nostri progetti</a> di @nerdalquadrato!\n\n"
                f"<i>📌 In qualità di Affiliati Amazon, riceviamo un guadagno dagli acquisti idonei.</i>"
            )
            
            await update.message.reply_text(
                messaggio_finale, 
                parse_mode=ParseMode.HTML, 
                disable_web_page_preview=True
            )

def main():
    """Inizializza e avvia il bot in modalità polling."""
    application = Application.builder().token(TOKEN_TELEGRAM).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processa_messaggio))
    
    print("Bot avviato.")
    application.run_polling()

if __name__ == '__main__':
    main()
