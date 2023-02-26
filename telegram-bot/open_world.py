
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import base64
import json
import urllib.request
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

token = os.getenv('TELEGRAM_BOT')

valid_usernames = ["you telegram id"]
domain = "Your Domain"
uuid = "Your setup UUID"

async def start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text(
        f"Hey {update.effective_user.first_name}\nI'm your nokar to generate new vmess configurations base on updated sni(s) that are resolved under 50ms from each ISP.\n\nuse /update"    )


async def update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.message
    username = message.from_user.username
    if username not in valid_usernames:
        return await update.message.reply_text(f"You're not auth person!")
   
   
    await update.message.reply_text("\nGetting latest data from http://bot.sudoer.net/best.cf.iran ...\n")
    for line in urllib.request.urlopen("http://bot.sudoer.net/best.cf.iran"):
        await update.message.reply_text(line.split()[0].decode("utf-8")  + " ISP. " + "Config for copy/paste:\n\n\n" + config_generator(domain, uuid, line.split()[0].decode("utf-8"), line.split()[1].decode("utf-8")) + "\n" )
    
app = (
    ApplicationBuilder().token(token).build()
)


def config_generator(domain, uuid, operatorName="", ip=""):
    if ip == "":
        ip = domain
    name = domain + " " + operatorName        
    j = json.dumps({
        "v": "2", "ps": name, "add": ip, "port": "443", "id": uuid,
        "aid": "0", "net": "ws", "type": "none", "sni": domain,
        "host": domain, "path": "/", "tls": "tls"
    })
    return("vmess://" + base64.b64encode(j.encode('ascii')).decode('ascii'))

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("update", update))
app.run_polling()
