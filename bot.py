import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)


BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))


# =========================
# Render Health Server
# =========================

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


# =========================
# دکمه صفحه اصلی
# =========================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "📝 آزمون‌های آزمایشی مجموعه",
                callback_data="mock_exams"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 امتحان‌های نهایی",
                callback_data="final_exams"
            )
        ],
        [
            InlineKeyboardButton(
                "📖 جزوات",
                callback_data="notes"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 اطلاعیه‌ها",
                callback_data="news"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# /start
# =========================

async def start(update: Update, context):

    await update.message.reply_text(
        "🎓 به ربات رسمی آکادمی موحد خوش آمدید!\n\n"
        "لطفاً بخش موردنظر خود را انتخاب کنید:",
        reply_markup=main_menu()
    )


# =========================
# انتخاب پایه
# =========================

def grade_menu(prefix):

    keyboard = [
        [
            InlineKeyboardButton(
                "📘 دهم",
                callback_data=f"{prefix}_grade10"
            )
        ],
        [
            InlineKeyboardButton(
                "📗 یازدهم",
                callback_data=f"{prefix}_grade11"
            )
        ],
        [
            InlineKeyboardButton(
                "📕 دوازدهم",
                callback_data=f"{prefix}_grade12"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="home"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# انتخاب رشته
# =========================

def field_menu(prefix):

    keyboard = [
        [
            InlineKeyboardButton(
                "🧪 تجربی",
                callback_data=f"{prefix}_experimental"
            )
        ],
        [
            InlineKeyboardButton(
                "📐 ریاضی",
                callback_data=f"{prefix}_math"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 انسانی",
                callback_data=f"{prefix}_humanities"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="home"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# انتخاب نوع درس
# =========================

def lesson_type_menu(prefix):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎯 دروس اختصاصی",
                callback_data=f"{prefix}_special"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 دروس عمومی",
                callback_data=f"{prefix}_general"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="final_exams"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# دروس اختصاصی
# =========================

SPECIAL_SUBJECTS = {

    "experimental": [
        ("🧬 زیست‌شناسی", "biology"),
        ("🧪 شیمی", "chemistry"),
        ("⚡ فیزیک", "physics"),
        ("📐 ریاضی", "math"),
    ],

    "math": [
        ("📐 ریاضی", "math"),
        ("⚡ فیزیک", "physics"),
        ("🧪 شیمی", "chemistry"),
    ],

    "humanities": [
        ("📊 ریاضی و آمار", "math_stats"),
        ("💰 اقتصاد", "economics"),
        ("📚 علوم و فنون ادبی", "literary_sciences"),
        ("🕌 عربی، زبان قرآن", "arabic"),
        ("🏛️ تاریخ", "history"),
        ("🌍 جغرافیا", "geography"),
        ("👥 جامعه‌شناسی", "sociology"),
        ("🧠 فلسفه", "philosophy"),
        ("🧠 روان‌شناسی", "psychology"),
    ],
}


# =========================
# دروس عمومی
# =========================

GENERAL_SUBJECTS = [
    ("📖 فارسی و نگارش", "persian"),
    ("🕌 دین و زندگی", "religion"),
    ("🇬🇧 زبان انگلیسی", "english"),
    ("🕌 عربی، زبان قرآن", "arabic"),
]


# =========================
# منوی دروس
# =========================

def subjects_menu(field, lesson_type):

    if lesson_type == "special":
        subjects = SPECIAL_SUBJECTS.get(field, [])
    else:
        subjects = GENERAL_SUBJECTS

    keyboard = []

    for name, code in subjects:

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"subject_{field}_{lesson_type}_{code}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data=f"final_field_{field}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================
# سال‌های امتحان
# =========================

def years_menu(field, lesson_type, subject):

    years = [
        "۱۳۹۸",
        "۱۳۹۹",
        "۱۴۰۰",
        "۱۴۰۱",
        "۱۴۰۲",
        "۱۴۰۳",
        "۱۴۰۴",
    ]

    keyboard = []

    for year in years:

        keyboard.append([
            InlineKeyboardButton(
                year,
                callback_data=f"file_{field}_{lesson_type}_{subject}_{year}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data=f"subjects_{field}_{lesson_type}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================
# Callback Handler
# =========================

async def button_handler(update: Update, context):

    query = update.callback_query

    await query.answer()

    data = query.data


    # =========================
    # صفحه اصلی
    # =========================

    if data == "home":

        await query.edit_message_text(
            "🎓 آکادمی موحد\n\n"
            "لطفاً بخش موردنظر خود را انتخاب کنید:",
            reply_markup=main_menu()
        )


    # =========================
    # آزمون‌های آزمایشی مجموعه
    # =========================

    elif data == "mock_exams":

        await query.edit_message_text(
            "📝 آزمون‌های آزمایشی مجموعه\n\n"
            "پایه موردنظر را انتخاب کنید:",
            reply_markup=grade_menu("mock")
        )


    # =========================
    # امتحانات نهایی
    # =========================

    elif data == "final_exams":

        await query.edit_message_text(
            "📚 امتحان‌های نهایی\n\n"
            "رشته موردنظر را انتخاب کنید:",
            reply_markup=field_menu("final")
        )


    # =========================
    # انتخاب رشته نهایی
    # =========================

    elif data.startswith("final_") and data.endswith(
        ("experimental", "math", "humanities")
    ):

        field = data.replace("final_", "")

        field_names = {
            "experimental": "🧪 تجربی",
            "math": "📐 ریاضی",
            "humanities": "📚 انسانی",
        }

        await query.edit_message_text(
            f"📚 امتحان‌های نهایی\n\n"
            f"رشته: {field_names[field]}\n\n"
            "نوع درس را انتخاب کنید:",
            reply_markup=lesson_type_menu(
                f"final_field_{field}"
            )
        )


    # =========================
    # انتخاب دروس اختصاصی
    # =========================

    elif data.startswith("final_field_") and data.endswith("_special"):

        field = data.replace(
            "final_field_", ""
        ).replace("_special", "")

        await query.edit_message_text(
            "🎯 دروس اختصاصی\n\n"
            "درس موردنظر را انتخاب کنید:",
            reply_markup=subjects_menu(
                field,
                "special"
            )
        )


    # =========================
    # انتخاب دروس عمومی
    # =========================

    elif data.startswith("final_field_") and data.endswith("_general"):

        field = data.replace(
            "final_field_", ""
        ).replace("_general", "")

        await query.edit_message_text(
            "📚 دروس عمومی\n\n"
            "درس موردنظر را انتخاب کنید:",
            reply_markup=subjects_menu(
                field,
                "general"
            )
        )


    # =========================
    # انتخاب درس
    # =========================

    elif data.startswith("subject_"):

        parts = data.split("_")

        field = parts[1]
        lesson_type = parts[2]
        subject = "_".join(parts[3:])

        await query.edit_message_text(
            "📚 انتخاب سال امتحان\n\n"
            "سال موردنظر را انتخاب کنید:",
            reply_markup=years_menu(
                field,
                lesson_type,
                subject
            )
        )


    # =========================
    # انتخاب سال
    # =========================

    elif data.startswith("file_"):

        parts = data.split("_")

        field = parts[1]
        lesson_type = parts[2]
        subject = "_".join(parts[3:-1])
        year = parts[-1]

        await query.edit_message_text(
            f"📄 امتحان نهایی\n\n"
            f"سال: {year}\n"
            f"درس: {subject}\n\n"
            "⏳ فایل این بخش هنوز به ربات متصل نشده است.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ بازگشت",
                        callback_data=f"subject_{field}_{lesson_type}_{subject}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 صفحه اصلی",
                        callback_data="home"
                    )
                ]
            ])
        )


    # =========================
    # جزوات
    # =========================

    elif data == "notes":

        await query.edit_message_text(
            "📖 جزوات\n\n"
            "این بخش به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 صفحه اصلی",
                        callback_data="home"
                    )
                ]
            ])
        )


    # =========================
    # اطلاعیه‌ها
    # =========================

    elif data == "news":

        await query.edit_message_text(
            "📢 اطلاعیه‌ها\n\n"
            "این بخش به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 صفحه اصلی",
                        callback_data="home"
                    )
                ]
            ])
        )


    # =========================
    # بخش آزمون‌های آزمایشی
    # =========================

    elif data.startswith("mock_"):

        await query.edit_message_text(
            "📝 آزمون‌های آزمایشی مجموعه\n\n"
            "این بخش در حال آماده‌سازی است.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🏠 صفحه اصلی",
                        callback_data="home"
                    )
                ]
            ])
        )


# =========================
# Main
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
