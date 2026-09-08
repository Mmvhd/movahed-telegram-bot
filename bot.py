import os
import json
import base64
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError


# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

PORT = int(os.environ.get("PORT", 10000))

ADMIN_ID = 7847705597

# کانال خصوصی آرشیو فایل‌ها
ARCHIVE_CHAT_ID = -1003919894012

# GitHub
GITHUB_OWNER = "Mmvhd"
GITHUB_REPO = "movahed-telegram-bot"
GITHUB_BRANCH = "main"
GITHUB_FILE = "files.json"

GITHUB_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
)


# =========================================================
# Render Health Server
# =========================================================

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


# =========================================================
# اطلاعات دروس
# =========================================================

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


GENERAL_SUBJECTS = [
    ("📖 فارسی و نگارش", "persian"),
    ("🕌 دین و زندگی", "religion"),
    ("🇬🇧 زبان انگلیسی", "english"),
    ("🕌 عربی، زبان قرآن", "arabic"),
]


FIELD_NAMES = {
    "experimental": "🧪 تجربی",
    "math": "📐 ریاضی",
    "humanities": "📚 انسانی",
}

GRADE_NAMES = {
    "grade10": "📘 دهم",
    "grade11": "📗 یازدهم",
    "grade12": "📕 دوازدهم",
}

LESSON_TYPE_NAMES = {
    "special": "🎯 اختصاصی",
    "general": "📚 عمومی",
}


YEARS = [
    "۱۳۹۸",
    "۱۳۹۹",
    "۱۴۰۰",
    "۱۴۰۱",
    "۱۴۰۲",
    "۱۴۰۳",
    "۱۴۰۴",
]


# =========================================================
# منوی اصلی
# =========================================================

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


# =========================================================
# /start
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎓 به ربات رسمی آکادمی موحد خوش آمدید!\n\n"
        "لطفاً بخش موردنظر خود را انتخاب کنید:",
        reply_markup=main_menu()
    )


# =========================================================
# منوی رشته
# =========================================================

def field_menu(prefix="final"):

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


# =========================================================
# منوی پایه
# =========================================================

def grade_menu(prefix="final"):

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
                callback_data="final_exams"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# نوع درس
# =========================================================

def lesson_type_menu(field):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎯 دروس اختصاصی",
                callback_data=f"final_type_{field}_special"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 دروس عمومی",
                callback_data=f"final_type_{field}_general"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data=f"final_{field}"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# منوی دروس
# =========================================================

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
                callback_data=(
                    f"subject_{field}_{lesson_type}_{code}"
                )
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data=f"final_grade_{field}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# منوی سال‌ها
# =========================================================

def years_menu(field, grade, lesson_type, subject):

    keyboard = []

    for year in YEARS:

        keyboard.append([
            InlineKeyboardButton(
                year,
                callback_data=(
                    f"file_{field}_{grade}_{lesson_type}_"
                    f"{subject}_{year}"
                )
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ بازگشت",
            callback_data=(
                f"subjects_{field}_{grade}_{lesson_type}"
            )
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# GitHub: خواندن files.json
# =========================================================

def github_get_files():

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(
        GITHUB_API,
        headers=headers,
        params={"ref": GITHUB_BRANCH},
        timeout=20,
    )

    if response.status_code == 404:
        return {}, None

    response.raise_for_status()

    data = response.json()

    content = data.get("content", "")
    sha = data.get("sha")

    if not content:
        return {}, sha

    decoded = base64.b64decode(
        content.replace("\n", "")
    ).decode("utf-8")

    try:
        files = json.loads(decoded)
    except json.JSONDecodeError:
        files = {}

    return files, sha


# =========================================================
# GitHub: ذخیره files.json
# =========================================================

def github_save_files(files, sha=None):

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    content = json.dumps(
        files,
        ensure_ascii=False,
        indent=2,
    )

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": "Update academy files",
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        GITHUB_API,
        headers=headers,
        json=payload,
        timeout=20,
    )

    response.raise_for_status()


# =========================================================
# کلید یکتا برای هر فایل
# =========================================================

def make_file_key(
    field,
    grade,
    lesson_type,
    subject,
    year
):

    return (
        f"{field}|"
        f"{grade}|"
        f"{lesson_type}|"
        f"{subject}|"
        f"{year}"
    )


# =========================================================
# Callback اصلی کاربران
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data


    # -------------------------
    # صفحه اصلی
    # -------------------------

    if data == "home":

        await query.edit_message_text(
            "🎓 آکادمی موحد\n\n"
            "لطفاً بخش موردنظر خود را انتخاب کنید:",
            reply_markup=main_menu()
        )
        return


    # -------------------------
    # آزمون‌های آزمایشی
    # -------------------------

    if data == "mock_exams":

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
        return


    # -------------------------
    # امتحانات نهایی
    # -------------------------

    if data == "final_exams":

        await query.edit_message_text(
            "📚 امتحان‌های نهایی\n\n"
            "رشته موردنظر را انتخاب کنید:",
            reply_markup=field_menu()
        )
        return


    # -------------------------
    # انتخاب رشته
    # -------------------------

    if data.startswith("final_") and data.count("_") == 1:

        field = data.replace("final_", "")

        if field in FIELD_NAMES:

            await query.edit_message_text(
                "📚 امتحان‌های نهایی\n\n"
                f"رشته: {FIELD_NAMES[field]}\n\n"
                "پایه موردنظر را انتخاب کنید:",
                reply_markup=grade_menu(
                    f"final_{field}"
                )
            )

        return


    # -------------------------
    # انتخاب پایه
    # -------------------------

    if data.startswith("final_") and "_grade" in data:

        parts = data.split("_")

        field = parts[1]
        grade = parts[2]

        if field in FIELD_NAMES:

            await query.edit_message_text(
                "📚 امتحان‌های نهایی\n\n"
                f"رشته: {FIELD_NAMES[field]}\n"
                f"پایه: {GRADE_NAMES[grade]}\n\n"
                "نوع درس را انتخاب کنید:",
                reply_markup=lesson_type_menu(
                    f"{field}_{grade}"
                )
            )

        return


    # -------------------------
    # انتخاب نوع درس
    # -------------------------

    if data.startswith("final_type_"):

        parts = data.split("_")

        field = parts[2]
        grade = parts[3]
        lesson_type = parts[4]

        await query.edit_message_text(
            "📚 انتخاب درس\n\n"
            f"رشته: {FIELD_NAMES[field]}\n"
            f"پایه: {GRADE_NAMES[grade]}\n"
            f"نوع: {LESSON_TYPE_NAMES[lesson_type]}\n\n"
            "درس موردنظر را انتخاب کنید:",
            reply_markup=subjects_menu(
                field,
                lesson_type
            )
        )

        # ذخیره پایه برای ادامه مسیر
        context.user_data["current_grade"] = grade

        return


    # -------------------------
    # انتخاب درس
    # -------------------------

    if data.startswith("subject_"):

        parts = data.split("_")

        field = parts[1]
        lesson_type = parts[2]
        subject = "_".join(parts[3:])

        grade = context.user_data.get(
            "current_grade"
        )

        if not grade:
            await query.edit_message_text(
                "⚠️ اطلاعات پایه پیدا نشد.\n"
                "لطفاً دوباره از ابتدا وارد شوید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🏠 صفحه اصلی",
                            callback_data="home"
                        )
                    ]
                ])
            )
            return

        await query.edit_message_text(
            "📚 انتخاب سال امتحان\n\n"
            f"رشته: {FIELD_NAMES[field]}\n"
            f"پایه: {GRADE_NAMES[grade]}\n"
            f"درس: {subject}\n\n"
            "سال موردنظر را انتخاب کنید:",
            reply_markup=years_menu(
                field,
                grade,
                lesson_type,
                subject
            )
        )

        return


    # -------------------------
    # انتخاب سال و ارسال فایل
    # -------------------------

    if data.startswith("file_"):

        parts = data.split("_")

        field = parts[1]
        grade = parts[2]
        lesson_type = parts[3]

        subject = "_".join(
            parts[4:-1]
        )

        year = parts[-1]

        key = make_file_key(
            field,
            grade,
            lesson_type,
            subject,
            year
        )

        try:
            files, _ = github_get_files()
        except Exception:
            await query.edit_message_text(
                "⚠️ خطا در دریافت اطلاعات فایل.\n"
                "لطفاً کمی بعد دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🏠 صفحه اصلی",
                            callback_data="home"
                        )
                    ]
                ])
            )
            return

        file_info = files.get(key)

        if not file_info:

            await query.edit_message_text(
                "📄 فایل موردنظر\n\n"
                f"رشته: {FIELD_NAMES[field]}\n"
                f"پایه: {GRADE_NAMES[grade]}\n"
                f"درس: {subject}\n"
                f"سال: {year}\n\n"
                "❌ فایل این بخش هنوز اضافه نشده است.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data=(
                                f"subject_{field}_"
                                f"{lesson_type}_{subject}"
                            )
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
            return

        archive_message_id = file_info.get(
            "archive_message_id"
        )

        try:

            await context.bot.copy_message(
                chat_id=query.from_user.id,
                from_chat_id=ARCHIVE_CHAT_ID,
                message_id=archive_message_id,
            )

        except TelegramError:

            await query.message.reply_text(
                "⚠️ در ارسال فایل مشکلی پیش آمد.\n"
                "لطفاً دوباره تلاش کنید."
            )

        return


    # -------------------------
    # جزوات
    # -------------------------

    if data == "notes":

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
        return


    # -------------------------
    # اطلاعیه‌ها
    # -------------------------

    if data == "news":

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
        return


# =========================================================
# پنل مدیریت
# =========================================================

def admin_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ افزودن فایل",
                callback_data="admin_add"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 صفحه اصلی ربات",
                callback_data="home"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👑 پنل مدیریت آکادمی موحد\n\n"
        "بخش موردنظر را انتخاب کنید:",
        reply_markup=admin_menu()
    )

    return ConversationHandler.END


# =========================================================
# مراحل افزودن فایل
# =========================================================

ADD_FIELD = 1
ADD_GRADE = 2
ADD_TYPE = 3
ADD_SUBJECT = 4
ADD_YEAR = 5
ADD_FILE = 6


async def admin_add_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "⛔ دسترسی غیرمجاز.",
            show_alert=True
        )
        return ConversationHandler.END

    await query.answer()

    await query.edit_message_text(
        "➕ افزودن فایل\n\n"
        "رشته را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🧪 تجربی",
                    callback_data="addfield_experimental"
                )
            ],
            [
                InlineKeyboardButton(
                    "📐 ریاضی",
                    callback_data="addfield_math"
                )
            ],
            [
                InlineKeyboardButton(
                    "📚 انسانی",
                    callback_data="addfield_humanities"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="admin_cancel"
                )
            ],
        ])
    )

    return ADD_FIELD


async def admin_select_field(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    field = query.data.replace(
        "addfield_", ""
    )

    context.user_data["add_field"] = field

    await query.edit_message_text(
        "➕ افزودن فایل\n\n"
        f"رشته: {FIELD_NAMES[field]}\n\n"
        "پایه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📘 دهم",
                    callback_data="addgrade_grade10"
                )
            ],
            [
                InlineKeyboardButton(
                    "📗 یازدهم",
                    callback_data="addgrade_grade11"
                )
            ],
            [
                InlineKeyboardButton(
                    "📕 دوازدهم",
                    callback_data="addgrade_grade12"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="admin_cancel"
                )
            ],
        ])
    )

    return ADD_GRADE


async def admin_select_grade(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    grade = query.data.replace(
        "addgrade_", ""
    )

    context.user_data["add_grade"] = grade

    await query.edit_message_text(
        "➕ افزودن فایل\n\n"
        f"رشته: "
        f"{FIELD_NAMES[context.user_data['add_field']]}\n"
        f"پایه: {GRADE_NAMES[grade]}\n\n"
        "نوع درس را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎯 اختصاصی",
                    callback_data="addtype_special"
                )
            ],
            [
                InlineKeyboardButton(
                    "📚 عمومی",
                    callback_data="addtype_general"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="admin_cancel"
                )
            ],
        ])
    )

    return ADD_TYPE


async def admin_select_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    lesson_type = query.data.replace(
        "addtype_", ""
    )

    context.user_data["add_type"] = lesson_type

    field = context.user_data["add_field"]

    if lesson_type == "special":
        subjects = SPECIAL_SUBJECTS.get(
            field,
            []
        )
    else:
        subjects = GENERAL_SUBJECTS

    keyboard = []

    for name, code in subjects:

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"addsubject_{code}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "❌ لغو",
            callback_data="admin_cancel"
        )
    ])

    await query.edit_message_text(
        "➕ افزودن فایل\n\n"
        f"رشته: {FIELD_NAMES[field]}\n"
        f"پایه: "
        f"{GRADE_NAMES[context.user_data['add_grade']]}\n"
        f"نوع: "
        f"{LESSON_TYPE_NAMES[lesson_type]}\n\n"
        "درس را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADD_SUBJECT


async def admin_select_subject(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    subject = query.data.replace(
        "addsubject_", ""
    )

    context.user_data["add_subject"] = subject

    keyboard = []

    for year in YEARS:

        keyboard.append([
            InlineKeyboardButton(
                year,
                callback_data=f"addyear_{year}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "❌ لغو",
            callback_data="admin_cancel"
        )
    ])

    await query.edit_message_text(
        "➕ افزودن فایل\n\n"
        f"درس: {subject}\n\n"
        "سال امتحان را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADD_YEAR


async def admin_select_year(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    year = query.data.replace(
        "addyear_", ""
    )

    context.user_data["add_year"] = year

    field = context.user_data["add_field"]
    grade = context.user_data["add_grade"]
    lesson_type = context.user_data["add_type"]
    subject = context.user_data["add_subject"]

    await query.edit_message_text(
        "📤 فایل را ارسال کنید.\n\n"
        f"رشته: {FIELD_NAMES[field]}\n"
        f"پایه: {GRADE_NAMES[grade]}\n"
        f"نوع: {LESSON_TYPE_NAMES[lesson_type]}\n"
        f"درس: {subject}\n"
        f"سال: {year}\n\n"
        "فایل را همینجا به صورت Document/PDF ارسال کنید.\n\n"
        "برای لغو، /cancel را بزنید."
    )

    return ADD_FILE


async def admin_receive_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )

        return ConversationHandler.END


    message = update.message

    if not message:

        return ADD_FILE


    # فقط پیام‌هایی که قابل کپی هستند
    if not (
        message.document
        or message.photo
        or message.video
        or message.audio
        or message.voice
    ):

        await message.reply_text(
            "⚠️ لطفاً خود فایل را ارسال کن.\n\n"
            "ترجیحاً PDF را به صورت Document بفرست."
        )

        return ADD_FILE


    field = context.user_data.get(
        "add_field"
    )

    grade = context.user_data.get(
        "add_grade"
    )

    lesson_type = context.user_data.get(
        "add_type"
    )

    subject = context.user_data.get(
        "add_subject"
    )

    year = context.user_data.get(
        "add_year"
    )


    if not all([
        field,
        grade,
        lesson_type,
        subject,
        year,
    ]):

        await message.reply_text(
            "⚠️ اطلاعات این فایل ناقص است.\n"
            "لطفاً دوباره از /admin شروع کن."
        )

        return ConversationHandler.END


    await message.reply_text(
        "⏳ فایل در حال ذخیره‌سازی در آرشیو است..."
    )


    key = make_file_key(
        field,
        grade,
        lesson_type,
        subject,
        year
    )


    try:

        # -------------------------------------------------
        # خواندن اطلاعات قبلی
        # -------------------------------------------------

        files, sha = github_get_files()


        # -------------------------------------------------
        # اگر فایل قبلی وجود دارد، پیام قبلی را حذف کن
        # -------------------------------------------------

        old_file = files.get(key)

        if old_file:

            old_message_id = old_file.get(
                "archive_message_id"
            )

            if old_message_id:

                try:

                    await context.bot.delete_message(
                        chat_id=ARCHIVE_CHAT_ID,
                        message_id=old_message_id
                    )

                except TelegramError:
                    pass


        # -------------------------------------------------
        # کپی فایل به کانال آرشیو
        # -------------------------------------------------

        copied = await context.bot.copy_message(
            chat_id=ARCHIVE_CHAT_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
        )


        archive_message_id = copied.message_id


        # -------------------------------------------------
        # ذخیره اطلاعات
        # -------------------------------------------------

        files[key] = {
            "field": field,
            "grade": grade,
            "lesson_type": lesson_type,
            "subject": subject,
            "year": year,
            "archive_chat_id": ARCHIVE_CHAT_ID,
            "archive_message_id": archive_message_id,
        }


        github_save_files(
            files,
            sha
        )


        await message.reply_text(
            "✅ فایل با موفقیت ثبت شد!\n\n"
            f"رشته: {FIELD_NAMES[field]}\n"
            f"پایه: {GRADE_NAMES[grade]}\n"
            f"نوع: {LESSON_TYPE_NAMES[lesson_type]}\n"
            f"درس: {subject}\n"
            f"سال: {year}\n\n"
            "📂 فایل در کانال آرشیو ذخیره شد.\n"
            "🗂️ اطلاعات آن در GitHub ثبت شد."
        )


    except Exception as error:

        print(
            "ERROR ADDING FILE:",
            repr(error)
        )

        await message.reply_text(
            "❌ ذخیره فایل انجام نشد.\n\n"
            "احتمالاً یکی از این موارد مشکل دارد:\n"
            "• دسترسی ربات به کانال آرشیو\n"
            "• توکن GitHub\n"
            "• دسترسی GitHub به Repository\n\n"
            "جزئیات خطا در Logs قابل مشاهده است."
        )


    context.user_data.clear()

    return ConversationHandler.END


async def admin_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    context.user_data.clear()

    await query.edit_message_text(
        "❌ عملیات لغو شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "👑 پنل مدیریت",
                    callback_data="admin_panel"
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

    return ConversationHandler.END


async def admin_panel_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی غیرمجاز.",
            show_alert=True
        )
        return

    await query.answer()

    await query.edit_message_text(
        "👑 پنل مدیریت آکادمی موحد\n\n"
        "بخش موردنظر را انتخاب کنید:",
        reply_markup=admin_menu()
    )


# =========================================================
# Main
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set"
        )

    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN is not set"
        )


    # Render health server
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()


    # Telegram application
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    # -----------------------------------------------------
    # پنل مدیریت
    # -----------------------------------------------------

    admin_conversation = ConversationHandler(

        entry_points=[
            CommandHandler(
                "admin",
                admin_command
            ),
            CallbackQueryHandler(
                admin_add_start,
                pattern="^admin_add$"
            ),
        ],

        states={

            ADD_FIELD: [
                CallbackQueryHandler(
                    admin_select_field,
                    pattern="^addfield_"
                ),
                CallbackQueryHandler(
                    admin_cancel,
                    pattern="^admin_cancel$"
                ),
            ],

            ADD_GRADE: [
                CallbackQueryHandler(
                    admin_select_grade,
                    pattern="^addgrade_"
                ),
                CallbackQueryHandler(
                    admin_cancel,
                    pattern="^admin_cancel$"
                ),
            ],

            ADD_TYPE: [
                CallbackQueryHandler(
                    admin_select_type,
                    pattern="^addtype_"
                ),
                CallbackQueryHandler(
                    admin_cancel,
                    pattern="^admin_cancel$"
                ),
            ],

            ADD_SUBJECT: [
                CallbackQueryHandler(
                    admin_select_subject,
                    pattern="^addsubject_"
                ),
                CallbackQueryHandler(
                    admin_cancel,
                    pattern="^admin_cancel$"
                ),
            ],

            ADD_YEAR: [
                CallbackQueryHandler(
                    admin_select_year,
                    pattern="^addyear_"
                ),
                CallbackQueryHandler(
                    admin_cancel,
                    pattern="^admin_cancel$"
                ),
            ],

            ADD_FILE: [
                MessageHandler(
                    filters.ALL
                    & ~filters.COMMAND,
                    admin_receive_file
                ),
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                admin_cancel
            ),
            CallbackQueryHandler(
                admin_cancel,
                pattern="^admin_cancel$"
            ),
        ],
    )


    app.add_handler(
        admin_conversation
    )


    # -----------------------------------------------------
    # Callback پنل مدیریت
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            admin_panel_callback,
            pattern="^admin_panel$"
        )
    )


    # -----------------------------------------------------
    # /start
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    # -----------------------------------------------------
    # سایر دکمه‌ها
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    print(
        "Movahed Academy Bot is running..."
    )


    app.run_polling()


if __name__ == "__main__":
    main()
