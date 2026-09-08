import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# آیدی عددی ادمین ربات را بعداً اینجا قرار می‌دهیم
ADMIN_ID = 0


# -------------------------
# Web Server برای Render
# -------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# -------------------------
# /start
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🎓 امتحان‌های آکادمی موحد", callback_data="academy")],
        [InlineKeyboardButton("📚 امتحان‌های نهایی", callback_data="final")],
        [InlineKeyboardButton("📖 جزوات", callback_data="notes")],
        [InlineKeyboardButton("🎯 منابع کنکور", callback_data="resources")],
        [InlineKeyboardButton("📢 اطلاعیه‌ها", callback_data="news")],
    ]

    await update.message.reply_text(
        "🎓 به ربات رسمی آکادمی موحد خوش آمدید!\n\n"
        "لطفاً بخش موردنظر خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# -------------------------
# دکمه‌ها
# -------------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # صفحه اصلی
    if data == "home":
        keyboard = [
            [InlineKeyboardButton("🎓 امتحان‌های آکادمی موحد", callback_data="academy")],
            [InlineKeyboardButton("📚 امتحان‌های نهایی", callback_data="final")],
            [InlineKeyboardButton("📖 جزوات", callback_data="notes")],
            [InlineKeyboardButton("🎯 منابع کنکور", callback_data="resources")],
            [InlineKeyboardButton("📢 اطلاعیه‌ها", callback_data="news")],
        ]

        await query.edit_message_text(
            "🎓 آکادمی موحد\n\n"
            "لطفاً بخش موردنظر خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # امتحان‌های نهایی
    elif data == "final":

        keyboard = [
            [InlineKeyboardButton("🧪 تجربی", callback_data="field_experimental")],
            [InlineKeyboardButton("📐 ریاضی", callback_data="field_math")],
            [InlineKeyboardButton("📚 انسانی", callback_data="field_humanities")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="home")],
        ]

        await query.edit_message_text(
            "📚 امتحان‌های نهایی\n\n"
            "رشته خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # رشته تجربی
    elif data == "field_experimental":

        keyboard = [
            [InlineKeyboardButton("🧬 زیست‌شناسی", callback_data="subject_biology")],
            [InlineKeyboardButton("🧪 شیمی", callback_data="subject_chemistry")],
            [InlineKeyboardButton("⚡ فیزیک", callback_data="subject_physics")],
            [InlineKeyboardButton("📐 ریاضی", callback_data="subject_math")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="final")],
        ]

        await query.edit_message_text(
            "🧪 رشته تجربی\n\n"
            "درس موردنظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # زیست
    elif data == "subject_biology":

        keyboard = [
            [InlineKeyboardButton("📄 ۱۴۰۴", callback_data="biology_1404")],
            [InlineKeyboardButton("📄 ۱۴۰۳", callback_data="biology_1403")],
            [InlineKeyboardButton("📄 ۱۴۰۲", callback_data="biology_1402")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="field_experimental")],
        ]

        await query.edit_message_text(
            "🧬 زیست‌شناسی\n\n"
            "سال موردنظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # فایل زیست ۱۴۰۴
    elif data == "biology_1404":

        await query.edit_message_text(
            "📄 زیست‌شناسی دوازدهم\n"
            "امتحان نهایی ۱۴۰۴\n\n"
            "⏳ فایل این بخش به‌زودی متصل می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="subject_biology")],
                [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="home")],
            ]),
        )

    # سال‌های فعلاً بدون فایل
    elif data in ["biology_1403", "biology_1402"]:

        await query.edit_message_text(
            "📄 فایل این سال هنوز اضافه نشده است.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="subject_biology")],
                [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="home")],
            ]),
        )

    # بخش‌های آینده
    elif data in ["academy", "notes", "resources", "news"]:

        await query.edit_message_text(
            "🚧 این بخش در حال آماده‌سازی است.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="home")],
            ]),
        )


# -------------------------
# اجرای ربات
# -------------------------

def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )
    web_thread.start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
