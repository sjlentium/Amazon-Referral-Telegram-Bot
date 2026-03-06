import re
import httpx
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- CONFIGURAZIONE ---
TOKEN_TELEGRAM = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN_TELEGRAM:
    raise ValueError("Errore: TELEGRAM_BOT_TOKEN non impostato nelle variabili d'ambiente.")

REFERRAL_TAG = "nerdalquadr0b-21"
MAX_URLS_PER_MESSAGGIO = 5
# ----------------------

async def estrai_asin_e_dominio(url: str) -> tuple[str, bool]:
    """
    Valida il dominio, risolve gli short link in modo asincrono,
    estrae l'ASIN a 10 caratteri e verifica se lo store è italiano.
    Restituisce una tupla: (asin, is_italiano).
    """
    try:
        parsed_url = urlparse(url)
        dominio = parsed_url.netloc.lower()
    except Exception:
        return None, False

    # Inclusi domini esteri per poter intercettare l'errore e avvisare l'utente
    domini_validi_amazon = [
        "amazon.it", "www.amazon.it", 
        "amazon.com", "www.amazon.com", 
        "amazon.co.uk", "www.amazon.co.uk", 
        "amazon.de", "amazon.fr", "amazon.es"
    ]
    domini_short = ["amzn.to", "amzn.eu"]
    
    # Se il dominio non è tra quelli consentiti, interrompiamo l'elaborazione
    if not any(dominio.endswith(d) for d in domini_validi_amazon + domini_short):
        return None, False

    url_finale = url

    # Fase 1: Risoluzione short link in modo ASINCRONO non bloccante
    if any(dominio.endswith(d) for d in domini_short):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    follow_redirects=True, 
                    timeout=5.0
                )
                url_finale = str(response.url)
                dominio = urlparse(url_finale).netloc.lower()
        except Exception:
            return None, False

    # Verifichiamo se lo store di destinazione è italiano
    is_italiano = dominio.endswith("amazon.it")

    # Fase 2: Estrazione ASIN tramite Regex
    pattern = r"(?:/dp/|/gp/product/|/exec/obidos/ASIN/|/o/ASIN/|/as/|/p/)(?P<asin>[A-Z0-9]{10})"
    match = re.search(pattern, url_finale, re.IGNORECASE)
    
    if match:
        return match.group("asin"), is_italiano
        
    return None, False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start inviando il messaggio di benvenuto."""
    messaggio_benvenuto = (
        f"🔗 <b>Mandami il link <a href=\"https://amzn.to/4cZjQYd\">Amazon</a> desiderato!</b>\n\n"
        f"In questo modo <b>contribuirai gratuitamente</b> a mantenere in vita i <a href=\"https://nerdalquadrato.it\">nostri progetti</a> di @nerdalquadrato!\n\n"
        f"<i>📌 In qualità di Affiliati Amazon, riceviamo un guadagno dagli acquisti idonei.</i>"
    )
    await update.message.reply_text(
        messaggio_benvenuto, 
        parse_mode=ParseMode.HTML, 
        disable_web_page_preview=True
    )

async def processa_messaggio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Intercetta i messaggi, esegue il parsing sicuro degli URL e restituisce il link pulito
    o un avviso se lo store non è italiano. Include la gestione degli errori per dare sempre feedback.
    """
    testo_utente = update.message.text
    
    # Identifica tutti gli URL presenti nel testo
    urls_trovati = re.findall(r'(https?://[^\s]+)', testo_utente)

    # Imposta un limite massimo di URL da processare
    if len(urls_trovati) > MAX_URLS_PER_MESSAGGIO:
        await update.message.reply_text(
            f"⚠️ <b>Troppi link!</b>\n\nPer evitare sovraccarichi, elaborerò solo i primi {MAX_URLS_PER_MESSAGGIO} link.",
            parse_mode=ParseMode.HTML
        )
        urls_trovati = urls_trovati[:MAX_URLS_PER_MESSAGGIO]
    
    # --- FEEDBACK 1: Nessun link trovato nel messaggio ---
    if not urls_trovati:
        await update.message.reply_text(
            "❌ <b>Nessun link rilevato.</b>\n\nAssicurati di inviarmi un link <a href=\"https://amzn.to/4cZjQYd\">Amazon</a> valido in modo che io possa processarlo!",
            parse_mode=ParseMode.HTML
        )
        return

    for url in urls_trovati:
        try:
            # Passiamo l'URL alla funzione asincrona di validazione ed estrazione
            asin, is_italiano = await estrai_asin_e_dominio(url)
            
            if asin:
                # Controllo validità geografica dello store
                if not is_italiano:
                    messaggio_errore = (
                        f"⚠️ Sembra che tu abbia inviato un link di uno <b>store estero</b>.\n"
                        f"Per supportarci, ti chiediamo di utilizzare un link di <b><a href=\"https://amzn.to/4cZjQYd\">Amazon Italia</a></b>."
                    )
                    await update.message.reply_text(
                        messaggio_errore,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    continue # Passa al prossimo URL se ce n'è più di uno nel messaggio

                # Fase 3: Ricostruzione normalizzata del link
                link_pulito = f"https://www.amazon.it/dp/{asin}?tag={REFERRAL_TAG}"
                
                messaggio_finale = (
                    f"✅ <b>Link Ottimizzato!</b>\n\n"
                    f"🛒 Acquista qui: <i>{link_pulito}</i>\n\n"
                    f"🔗 Manda un altro link quando vuoi, in questo modo <b>contribuirai gratuitamente</b> a mantenere in vita i <a href=\"https://nerdalquadrato.it\">nostri progetti</a> di @nerdalquadrato!\n\n"
                    f"<i>📌 In qualità di Affiliati Amazon, riceviamo un guadagno dagli acquisti idonei.</i>"
                )
                
                await update.message.reply_text(
                    messaggio_finale, 
                    parse_mode=ParseMode.HTML, 
                    disable_web_page_preview=True
                )
            else:
                # --- FEEDBACK 2: Link non supportato o ASIN inesistente ---
                await update.message.reply_text(
                    f"❌ <b>Link non supportato.</b>\nNon sono riuscito a trovare un prodotto <a href=\"https://amzn.to/4cZjQYd\">Amazon</a> valido in questo link:\n<i>{url}</i>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
        except Exception as e:
            # --- FEEDBACK 3: Errore di sistema imprevisto ---
            print(f"Errore imprevisto durante l'elaborazione del link {url}: {e}")
            await update.message.reply_text(
                "⚠️ <b>Ops! Qualcosa è andato storto.</b>\nSi è verificato un errore durante l'elaborazione del tuo link. Riprova più tardi.",
                parse_mode=ParseMode.HTML
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
