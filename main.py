import logging
import subprocess
import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ABOUT_ME = """
Ethical Hacking Bot by Senpai
GitHub: https://github.com/senpai80085
Website:
"""

JOIN_CHANNEL_URL = "https://t.me/your"

def main_menu():
    keyboard = [
        [InlineKeyboardButton("Nmap", callback_data='nmap')],
        [InlineKeyboardButton("Infoga", callback_data='infoga')],
        [InlineKeyboardButton("Hydra", callback_data='hydra')],
        [InlineKeyboardButton("John the Ripper", callback_data='john')],
        [InlineKeyboardButton("TheHarvester", callback_data='harvester')],
        [
            InlineKeyboardButton("Help", callback_data='help'),
            InlineKeyboardButton("About Me", callback_data='about')
        ],
        [InlineKeyboardButton("Join Channel", url=JOIN_CHANNEL_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Senpai's Ethical Hacking Bot!", reply_markup=main_menu())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use the buttons to access tools. Type /start to return to the menu.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_ME)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    context.user_data['tool'] = action

    prompts = {
        'nmap': "Send target IP or domain for Nmap scan:",
        'infoga': "Send email to run Infoga:",
        'hydra': "Hydra: Send target IP, port, and service (e.g., 192.168.1.1 22 ssh):",
        'john': "John: Upload hash file for cracking.",
        'harvester': "Send domain to run TheHarvester:"
    }

    if action in prompts:
        await query.edit_message_text(prompts[action])
    elif action == 'help':
        await query.edit_message_text("This bot uses open-source security tools. Use responsibly.", reply_markup=main_menu())
    elif action == 'about':
        await query.edit_message_text(ABOUT_ME, reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tool = context.user_data.get('tool')
    if not tool or tool == 'john':
        return

    args = update.message.text.strip()
    try:
        if tool == 'nmap':
            cmd = f"nmap {args}"
        elif tool == 'infoga':
            cmd = f"python3 tools/Infoga/infoga.py -t {args} -s all -v 2"
        elif tool == 'hydra':
            parts = args.split()
            if len(parts) != 3:
                raise ValueError("Format: IP PORT SERVICE")
            cmd = f"hydra -l admin -P /usr/share/wordlists/rockyou.txt -s {parts[1]} {parts[0]} {parts[2]}"
        elif tool == 'harvester':
            cmd = f"python3 tools/theHarvester/theHarvester.py -d {args} -b google"
        else:
            return

        result = subprocess.getoutput(cmd)
        await update.message.reply_text(f"Result from {tool}:
{result[:4000]}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        context.user_data['tool'] = None

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tool = context.user_data.get('tool')
    if tool != 'john':
        return

    file = await update.message.document.get_file()
    filename = f"uploads/{update.message.document.file_name}"
    await file.download_to_drive(filename)
    try:
        result = subprocess.getoutput(f"john --wordlist=/usr/share/wordlists/rockyou.txt {filename}")
        await update.message.reply_text(f"John Result:
{result[:4000]}")
    except Exception as e:
        await update.message.reply_text(f"Error running John: {e}")
    finally:
        context.user_data['tool'] = None

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('help', help_command))
app.add_handler(CommandHandler('about', about))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

if __name__ == '__main__':
    print("Bot is running...")
    app.run_polling()
