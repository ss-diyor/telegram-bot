import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, CallbackQueryHandler

TOKEN = '7250335187:AAHQWmK_zQniGa7DetIzre4iPPmWsq86xSw'
CHANNEL_ID = '@desmancy'
ADMIN_ID = 1746229472  # O'z ID raqamingizni yozing
PASSWORD = 'ss2026'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

pending = {}
approved_users = set()
waiting_password = set()

app = Flask('')

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in approved_users:
        update.message.reply_text("Siz allaqachon tizimga kirgansiz! Xabaringizni yuboring.")
    else:
        waiting_password.add(user_id)
        update.message.reply_text("Salom! Iltimos, parolni kiriting:")

def check_password(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in waiting_password:
        if update.message.text == PASSWORD:
            approved_users.add(user_id)
            waiting_password.discard(user_id)
            update.message.reply_text("Parol to'g'ri! Xabaringizni yuborishingiz mumkin.")
        else:
            update.message.reply_text("Parol noto'g'ri! Qaytadan urinib ko'ring.")
        return True
    return False

def forward_message(update: Update, context: CallbackContext):
    try:
        user_id = update.message.from_user.id

        # Parol kutilayotgan bo'lsa
        if check_password(update, context):
            return

        # Ruxsat yo'q
        if user_id not in approved_users:
            update.message.reply_text("Avval /start bosib parolni kiriting.")
            return

        msg = update.message
        user = msg.from_user
        user_info = f"👤 {user.first_name} (ID: {user.id})"

        key = f"{msg.chat_id}_{msg.message_id}"
        pending[key] = {
            "chat_id": msg.chat_id,
            "type": None,
            "content": None,
            "caption": msg.caption or ""
        }

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{key}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{key}")
            ]
        ])

        if msg.text:
            pending[key]["type"] = "text"
            pending[key]["content"] = msg.text
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"{user_info} dan xabar:\n\n{msg.text}",
                reply_markup=keyboard
            )
        elif msg.photo:
            pending[key]["type"] = "photo"
            pending[key]["content"] = msg.photo[-1].file_id
            context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=msg.photo[-1].file_id,
                caption=f"{user_info} dan rasm",
                reply_markup=keyboard
            )
        elif msg.video:
            pending[key]["type"] = "video"
            pending[key]["content"] = msg.video.file_id
            context.bot.send_video(
                chat_id=ADMIN_ID,
                video=msg.video.file_id,
                caption=f"{user_info} dan video",
                reply_markup=keyboard
            )
        elif msg.document:
            pending[key]["type"] = "document"
            pending[key]["content"] = msg.document.file_id
            context.bot.send_document(
                chat_id=ADMIN_ID,
                document=msg.document.file_id,
                caption=f"{user_info} dan fayl",
                reply_markup=keyboard
            )
        elif msg.voice:
            pending[key]["type"] = "voice"
            pending[key]["content"] = msg.voice.file_id
            context.bot.send_voice(
                chat_id=ADMIN_ID,
                voice=msg.voice.file_id,
                reply_markup=keyboard
            )
        else:
            return

        msg.reply_text("Xabaringiz adminga yuborildi, tasdiqlanishini kuting.")

    except Exception as e:
        logger.error("Xatolik: " + str(e))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    parts = data.split("_", 1)
    action = parts[0]
    key = parts[1]

    if key not in pending:
        query.edit_message_text("Bu xabar endi mavjud emas.")
        return

    msg_data = pending[key]
    chat_id = msg_data["chat_id"]
    msg_type = msg_data["type"]
    content = msg_data["content"]
    caption = msg_data["caption"]

    if action == "approve":
        try:
            if msg_type == "text":
                context.bot.send_message(chat_id=CHANNEL_ID, text=content)
            elif msg_type == "photo":
                context.bot.send_photo(chat_id=CHANNEL_ID, photo=content, caption=caption)
            elif msg_type == "video":
                context.bot.send_video(chat_id=CHANNEL_ID, video=content, caption=caption)
            elif msg_type == "document":
                context.bot.send_document(chat_id=CHANNEL_ID, document=content, caption=caption)
            elif msg_type == "voice":
                context.bot.send_voice(chat_id=CHANNEL_ID, voice=content)

            context.bot.send_message(chat_id=chat_id, text="Xabaringiz tasdiqlandi va kanalga yuborildi!")
            query.edit_message_text(query.message.text + "\n\n✅ Tasdiqlandi")
            del pending[key]

        except Exception as e:
            logger.error("Tasdiqlashda xatolik: " + str(e))

    elif action == "reject":
        context.bot.send_message(chat_id=chat_id, text="Xabaringiz rad etildi.")
        query.edit_message_text(query.message.text + "\n\n❌ Rad etildi")
        del pending[key]

def main():
    Thread(target=run_flask).start()
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(
        MessageHandler(
            (Filters.text | Filters.photo | Filters.video | Filters.document | Filters.voice) & ~Filters.command,
            forward_message
        )
    )
    print("Bot ishlayapti!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
