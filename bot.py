import os
import json
import base64
import logging
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
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# مدیر اصلی ربات
ADMIN_IDS = {7847705597}

# کانال آرشیو خصوصی
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

PORT = int(os.getenv("PORT", "10000"))


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# =========================================================
# RENDER HEALTH CHECK
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Movahed Telegram Bot is running.")

    def log_message(self, format, *args):
        return


def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================================================
# ADMIN
# =========================================================

def is_admin(update: Update) -> bool:
    user = update.effective_user

    if user is None:
        return False

    return user.id in ADMIN_IDS


# =========================================================
# DATA
# =========================================================

FIELDS = {
    "exp": "🔬 تجربی",
    "math": "📐 ریاضی",
    "hum": "📖 انسانی",
}

GRADES = {
    "11": "1️⃣1️⃣ یازدهم",
    "12": "1️⃣2️⃣ دوازدهم",
}

TYPES = {
    "general": "📘 عمومی",
    "special": "🧪 تخصصی",
}


# =========================================================
# SUBJECTS
# =========================================================

SUBJECTS = {

    # -----------------------------------------------------
    # تجربی
    # -----------------------------------------------------

    ("exp", "11", "general"): [
        ("دین و زندگی (۲)", "religion2"),
        ("فارسی (۲)", "persian2"),
        ("هنر (۲)", "art2"),
        ("عربی، زبان قرآن (۲)", "arabic2"),
        ("زبان انگلیسی (۲)", "english2"),
        ("تاریخ معاصر ایران", "contemporary_history"),
        ("انسان و محیط زیست", "human_environment"),
    ],

    ("exp", "11", "special"): [
        ("زیست‌شناسی (۲)", "biology2"),
        ("ریاضی (۲)", "math2"),
        ("شیمی (۲)", "chemistry2"),
        ("فیزیک (۲)", "physics2"),
        ("آزمایشگاه علوم تجربی (۲)", "science_lab2"),
        ("زمین‌شناسی", "geology"),
    ],

    ("exp", "12", "general"): [
        ("ادبیات فارسی (۳)", "persian3"),
        ("دین و زندگی (۳)", "religion3"),
        ("عربی، زبان قرآن (۳)", "arabic3"),
        ("هویت اجتماعی", "social_identity"),
        ("مدیریت خانواده و سبک زندگی", "family_lifestyle"),
        ("زبان انگلیسی (۳)", "english3"),
        ("سلامت و بهداشت", "health"),
    ],

    ("exp", "12", "special"): [
        ("زیست‌شناسی (۳)", "biology3"),
        ("ریاضی (۳)", "math3"),
        ("شیمی (۳)", "chemistry3"),
        ("فیزیک (۳)", "physics3"),
    ],


    # -----------------------------------------------------
    # ریاضی
    # -----------------------------------------------------

    ("math", "11", "general"): [
        ("ادبیات فارسی (۲)", "persian2"),
        ("دین و زندگی (۲)", "religion2"),
        ("عربی، زبان قرآن (۲)", "arabic2"),
        ("هنر (۲)", "art2"),
        ("تاریخ معاصر ایران (۲)", "contemporary_history2"),
        ("زبان انگلیسی (۲)", "english2"),
        ("تعلیمات ادیان الهی و اخلاق (۲)", "religious_ethics2"),
        ("زمین‌شناسی", "geology"),
        ("انسان و محیط زیست", "human_environment"),
    ],

    ("math", "11", "special"): [
        ("شیمی (۲)", "chemistry2"),
        ("فیزیک (۲)", "physics2"),
        ("هندسه (۲)", "geometry2"),
        ("حسابان (۱)", "calculus1"),
        ("آمار و احتمال", "statistics_probability"),
    ],

    ("math", "12", "general"): [
        ("ادبیات فارسی (۳)", "persian3"),
        ("دین و زندگی (۳)", "religion3"),
        ("عربی، زبان قرآن (۳)", "arabic3"),
        ("زبان انگلیسی (۳)", "english3"),
        ("تعلیمات ادیان الهی و اخلاق (۳)", "religious_ethics3"),
        ("سلامت و بهداشت", "health"),
        ("هویت اجتماعی", "social_identity"),
    ],

    ("math", "12", "special"): [
        ("شیمی (۳)", "chemistry3"),
        ("فیزیک (۳)", "physics3"),
        ("هندسه (۳)", "geometry3"),
        ("حسابان (۲)", "calculus2"),
        ("ریاضیات گسسته", "discrete_math"),
    ],


    # -----------------------------------------------------
    # انسانی
    # -----------------------------------------------------

    ("hum", "11", "general"): [
        ("فارسی (۲)", "persian2"),
        ("دین و زندگی (۲)", "religion2"),
        ("انسان و محیط زیست", "human_environment"),
        ("زبان انگلیسی (۲)", "english2"),
        ("هنر", "art"),
        ("مدیریت خانواده و سبک زندگی", "family_lifestyle"),
    ],

    ("hum", "11", "special"): [
        ("ریاضی و آمار (۲)", "math_statistics2"),
        ("عربی، زبان قرآن (۲)", "arabic2"),
        ("علوم و فنون ادبی (۲)", "literary_sciences2"),
        ("فلسفه", "philosophy"),
        ("تاریخ (۲)", "history2"),
        ("جغرافیای (۲)", "geography2"),
        ("جامعه‌شناسی (۲)", "sociology2"),
        ("روان‌شناسی", "psychology"),
    ],

    ("hum", "12", "general"): [
        ("فارسی (۳)", "persian3"),
        ("دین و زندگی (۳)", "religion3"),
        ("تحلیل فرهنگی", "cultural_analysis"),
        ("زبان انگلیسی (۳)", "english3"),
        ("سلامت و بهداشت", "health"),
        ("مدیریت خانواده و سبک زندگی", "family_lifestyle"),
    ],

    ("hum", "12", "special"): [
        ("ریاضی و آمار (۳)", "math_statistics3"),
        ("عربی، زبان قرآن (۳)", "arabic3"),
        ("علوم و فنون ادبی (۳)", "literary_sciences3"),
        ("فلسفه (۲)", "philosophy2"),
        ("تاریخ (۳)", "history3"),
        ("جغرافیای (۳)", "geography3"),
        ("جامعه‌شناسی (۳)", "sociology3"),
    ],
}


YEARS = [
    ("۱۴۰۴", "1404"),
    ("۱۴۰۳", "1403"),
    ("۱۴۰۲", "1402"),
    ("۱۴۰۱", "1401"),
    ("۱۴۰۰", "1400"),
    ("۱۳۹۹", "1399"),
    ("۱۳۹۸", "1398"),
]


# =========================================================
# GITHUB
# =========================================================

def github_headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2026-03-10",
    }


def github_get_files():
    """
    Returns:
        files_dict, sha
    """

    try:
        response = requests.get(
            GITHUB_API,
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=20,
        )

        if response.status_code == 404:
            return {}, None

        response.raise_for_status()

        data = response.json()

        encoded = data.get("content", "").replace("\n", "")

        if not encoded:
            return {}, data.get("sha")

        decoded = base64.b64decode(encoded).decode("utf-8")

        if not decoded.strip():
            return {}, data.get("sha")

        return json.loads(decoded), data.get("sha")

    except Exception:
        logger.exception("GitHub read error")
        return {}, None


def github_save_files(files, sha=None):
    """
    Create or update files.json on GitHub.
    """

    content = json.dumps(
        files,
        ensure_ascii=False,
        indent=2,
    )

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": "Update exam files metadata",
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        GITHUB_API,
        headers=github_headers(),
        json=payload,
        timeout=30,
    )

    if response.status_code not in (200, 201):
        logger.error(
            "GitHub save failed: %s %s",
            response.status_code,
            response.text,
        )

        return False

    return True


def make_file_key(field, grade, lesson_type, subject_code, year):
    return "|".join([
        field,
        grade,
        lesson_type,
        subject_code,
        year,
    ])


# =========================================================
# MAIN MENU
# =========================================================

def main_menu(update: Update):
    keyboard = [
        [
            InlineKeyboardButton(
                "📝 آزمون‌های آزمایشی مجموعه",
                callback_data="mock_exams",
            )
        ],
        [
            InlineKeyboardButton(
                "📚 امتحان‌های نهایی",
                callback_data="final_exams",
            )
        ],
        [
            InlineKeyboardButton(
                "📖 جزوات",
                callback_data="notes",
            )
        ],
        [
            InlineKeyboardButton(
                "📢 اطلاعیه‌ها",
                callback_data="news",
            )
        ],
    ]

    if is_admin(update):
        keyboard.append([
            InlineKeyboardButton(
                "👑 پنل مدیریت",
                callback_data="admin_panel",
            )
        ])

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    logger.info(
        "START | user_id=%s | username=%s | first_name=%s",
        user.id if user else None,
        user.username if user else None,
        user.first_name if user else None,
    )

    text = (
        "🎓 به آکادمی مشاوره موحد خوش آمدید.\n\n"
        "از منوی زیر بخش موردنظر را انتخاب کنید."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(update),
    )


# =========================================================
# FINAL EXAMS - USER SIDE
# =========================================================

def final_fields_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                FIELDS["exp"],
                callback_data="ufield_exp",
            )
        ],
        [
            InlineKeyboardButton(
                FIELDS["math"],
                callback_data="ufield_math",
            )
        ],
        [
            InlineKeyboardButton(
                FIELDS["hum"],
                callback_data="ufield_hum",
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ بازگشت",
                callback_data="home",
            )
        ],
    ])


def final_grades_keyboard(field):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                GRADES["11"],
                callback_data=f"ugrade_{field}_11",
            )
        ],
        [
            InlineKeyboardButton(
                GRADES["12"],
                callback_data=f"ugrade_{field}_12",
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ بازگشت",
                callback_data="final_exams",
            )
        ],
    ])


def final_types_keyboard(field, grade):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                TYPES["general"],
                callback_data=f"utype_{field}_{grade}_general",
            )
        ],
        [
            InlineKeyboardButton(
                TYPES["special"],
                callback_data=f"utype_{field}_{grade}_special",
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ بازگشت",
                callback_data=f"ufield_{field}",
            )
        ],
    ])


def subjects_keyboard(field, grade, lesson_type):
    subjects = SUBJECTS.get(
        (field, grade, lesson_type),
        [],
    )

    buttons = []

    for name, code in subjects:
        buttons.append([
            InlineKeyboardButton(
                name,
                callback_data=(
                    f"usub_{field}_{grade}_{lesson_type}_{code}"
                ),
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "↩️ بازگشت",
            callback_data=f"ugrade_{field}_{grade}",
        )
    ])

    return InlineKeyboardMarkup(buttons)


def years_keyboard(field, grade, lesson_type, subject_code):
    buttons = []

    for display_year, year_code in YEARS:
        buttons.append([
            InlineKeyboardButton(
                display_year,
                callback_data=(
                    f"uyear_{field}_{grade}_{lesson_type}_"
                    f"{subject_code}_{year_code}"
                ),
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "↩️ بازگشت",
            callback_data=(
                f"utype_{field}_{grade}_{lesson_type}"
            ),
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def show_final_exams(query):
    await query.edit_message_text(
        "📚 امتحان‌های نهایی\n\nرشته خود را انتخاب کنید:",
        reply_markup=final_fields_keyboard(),
    )


async def show_field(query, field):
    await query.edit_message_text(
        f"{FIELDS[field]}\n\nپایه را انتخاب کنید:",
        reply_markup=final_grades_keyboard(field),
    )


async def show_grade(query, field, grade):
    await query.edit_message_text(
        f"{FIELDS[field]} → {GRADES[grade]}\n\n"
        "نوع درس را انتخاب کنید:",
        reply_markup=final_types_keyboard(field, grade),
    )


async def show_type(query, field, grade, lesson_type):
    subjects = SUBJECTS.get(
        (field, grade, lesson_type),
        [],
    )

    if not subjects:
        await query.edit_message_text(
            "درسی برای این بخش ثبت نشده است.",
            reply_markup=final_types_keyboard(field, grade),
        )
        return

    await query.edit_message_text(
        f"{FIELDS[field]} → {GRADES[grade]}\n"
        f"{TYPES[lesson_type]}\n\n"
        "درس را انتخاب کنید:",
        reply_markup=subjects_keyboard(
            field,
            grade,
            lesson_type,
        ),
    )


async def show_subject(
    query,
    field,
    grade,
    lesson_type,
    subject_code,
):
    subject_name = next(
        (
            name
            for name, code in SUBJECTS.get(
                (field, grade, lesson_type),
                [],
            )
            if code == subject_code
        ),
        subject_code,
    )

    await query.edit_message_text(
        f"📚 {subject_name}\n\n"
        "سال امتحان را انتخاب کنید:",
        reply_markup=years_keyboard(
            field,
            grade,
            lesson_type,
            subject_code,
        ),
    )


async def send_exam_file(
    query,
    context,
    field,
    grade,
    lesson_type,
    subject_code,
    year,
):
    files, _ = github_get_files()

    key = make_file_key(
        field,
        grade,
        lesson_type,
        subject_code,
        year,
    )

    item = files.get(key)

    if not item:
        await query.edit_message_text(
            "❌ برای این درس و این سال هنوز فایلی ثبت نشده است.\n\n"
            "سال دیگری را انتخاب کنید.",
            reply_markup=years_keyboard(
                field,
                grade,
                lesson_type,
                subject_code,
            ),
        )
        return

    archive_message_id = item.get("archive_message_id")

    if not archive_message_id:
        await query.edit_message_text(
            "❌ اطلاعات فایل ناقص است و فایل آرشیو پیدا نشد.",
            reply_markup=years_keyboard(
                field,
                grade,
                lesson_type,
                subject_code,
            ),
        )
        return

    try:
        await context.bot.copy_message(
            chat_id=query.from_user.id,
            from_chat_id=ARCHIVE_CHAT_ID,
            message_id=int(archive_message_id),
        )

        await query.message.reply_text(
            "✅ فایل برای شما ارسال شد.",
            reply_markup=years_keyboard(
                field,
                grade,
                lesson_type,
                subject_code,
            ),
        )

    except Exception:
        logger.exception("File sending error")

        await query.message.reply_text(
            "❌ ارسال فایل انجام نشد.\n"
            "احتمالاً فایل آرشیو حذف شده یا دسترسی ربات به کانال مشکل دارد.",
            reply_markup=years_keyboard(
                field,
                grade,
                lesson_type,
                subject_code,
            ),
        )


# =========================================================
# ADMIN PANEL
# =========================================================

def admin_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ افزودن فایل",
                callback_data="admin_add",
            )
        ],
        [
            InlineKeyboardButton(
                "📊 وضعیت فایل‌ها",
                callback_data="admin_status",
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home",
            )
        ],
    ])


def admin_fields_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                FIELDS["exp"],
                callback_data="afield_exp",
            )
        ],
        [
            InlineKeyboardButton(
                FIELDS["math"],
                callback_data="afield_math",
            )
        ],
        [
            InlineKeyboardButton(
                FIELDS["hum"],
                callback_data="afield_hum",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data="admin_panel",
            )
        ],
    ])


def admin_grades_keyboard(field):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                GRADES["11"],
                callback_data=f"agrade_{field}_11",
            )
        ],
        [
            InlineKeyboardButton(
                GRADES["12"],
                callback_data=f"agrade_{field}_12",
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ بازگشت",
                callback_data="admin_add",
            )
        ],
    ])


def admin_types_keyboard(field, grade):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                TYPES["general"],
                callback_data=f"atype_{field}_{grade}_general",
            )
        ],
        [
            InlineKeyboardButton(
                TYPES["special"],
                callback_data=f"atype_{field}_{grade}_special",
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ بازگشت",
                callback_data=f"afield_{field}",
            )
        ],
    ])


def admin_subjects_keyboard(field, grade, lesson_type):
    subjects = SUBJECTS.get(
        (field, grade, lesson_type),
        [],
    )

    buttons = []

    for name, code in subjects:
        buttons.append([
            InlineKeyboardButton(
                name,
                callback_data=(
                    f"asub_{field}_{grade}_{lesson_type}_{code}"
                ),
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "↩️ بازگشت",
            callback_data=f"agrade_{field}_{grade}",
        )
    ])

    return InlineKeyboardMarkup(buttons)


def admin_years_keyboard(
    field,
    grade,
    lesson_type,
    subject_code,
):
    buttons = []

    for display_year, year_code in YEARS:
        buttons.append([
            InlineKeyboardButton(
                display_year,
                callback_data=(
                    f"ayear_{field}_{grade}_{lesson_type}_"
                    f"{subject_code}_{year_code}"
                ),
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "↩️ بازگشت",
            callback_data=(
                f"atype_{field}_{grade}_{lesson_type}"
            ),
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def admin_panel(update, context):
    if not is_admin(update):
        return

    query = update.callback_query

    await query.edit_message_text(
        "👑 پنل مدیریت\n\n"
        "از این قسمت می‌توانید فایل‌های امتحان نهایی را "
        "بدون دست‌زدن به کد اضافه یا جایگزین کنید.",
        reply_markup=admin_menu(),
    )


async def admin_add_start(update, context):
    if not is_admin(update):
        return

    query = update.callback_query

    await query.edit_message_text(
        "➕ افزودن فایل\n\n"
        "رشته را انتخاب کنید:",
        reply_markup=admin_fields_keyboard(),
    )


# =========================================================
# ADMIN CONVERSATION STATES
# =========================================================

ADMIN_FILE = 1


async def admin_receive_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update):
        return ConversationHandler.END

    message = update.message

    # قبول فایل به صورت Document
    if not message.document:
        await message.reply_text(
            "❌ لطفاً فایل را به صورت Document ارسال کن.\n\n"
            "مثلاً PDF را به صورت فایل بفرست، نه عکس."
        )

        return ADMIN_FILE

    data = context.user_data.get("admin_upload")

    if not data:
        await message.reply_text(
            "❌ اطلاعات مسیر فایل پیدا نشد.\n"
            "دوباره از پنل مدیریت شروع کن."
        )

        return ConversationHandler.END

    field = data["field"]
    grade = data["grade"]
    lesson_type = data["lesson_type"]
    subject_code = data["subject_code"]
    year = data["year"]

    # -----------------------------------------------------
    # Copy to archive channel
    # -----------------------------------------------------

    try:
        copied = await context.bot.copy_message(
            chat_id=ARCHIVE_CHAT_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
        )

        archive_message_id = copied.message_id

    except Exception:
        logger.exception("Archive copy error")

        await message.reply_text(
            "❌ فایل دریافت شد ولی نتوانستم آن را به "
            "کانال آرشیو منتقل کنم.\n\n"
            "دسترسی ربات به کانال آرشیو را بررسی کن."
        )

        return ConversationHandler.END

    # -----------------------------------------------------
    # Read GitHub
    # -----------------------------------------------------

    files, sha = github_get_files()

    key = make_file_key(
        field,
        grade,
        lesson_type,
        subject_code,
        year,
    )

    # -----------------------------------------------------
    # Delete previous archive message if replacing
    # -----------------------------------------------------

    old_item = files.get(key)

    if old_item:
        old_archive_id = old_item.get("archive_message_id")

        if old_archive_id:
            try:
                await context.bot.delete_message(
                    chat_id=ARCHIVE_CHAT_ID,
                    message_id=int(old_archive_id),
                )
            except Exception:
                logger.warning(
                    "Could not delete old archive message."
                )

    # -----------------------------------------------------
    # Subject name
    # -----------------------------------------------------

    subject_name = next(
        (
            name
            for name, code in SUBJECTS.get(
                (field, grade, lesson_type),
                [],
            )
            if code == subject_code
        ),
        subject_code,
    )

    # -----------------------------------------------------
    # Save metadata
    # -----------------------------------------------------

    files[key] = {
        "field": field,
        "field_name": FIELDS[field],
        "grade": grade,
        "grade_name": GRADES[grade],
        "lesson_type": lesson_type,
        "lesson_type_name": TYPES[lesson_type],
        "subject_code": subject_code,
        "subject_name": subject_name,
        "year": year,
        "archive_chat_id": ARCHIVE_CHAT_ID,
        "archive_message_id": archive_message_id,
        "file_name": message.document.file_name,
        "updated_by": update.effective_user.id,
    }

    success = github_save_files(
        files,
        sha,
    )

    if not success:
        # اگر GitHub ذخیره نشد، فایل آرشیو را پاک می‌کنیم
        # تا دیتای نصفه باقی نماند.
        try:
            await context.bot.delete_message(
                chat_id=ARCHIVE_CHAT_ID,
                message_id=archive_message_id,
            )
        except Exception:
            pass

        await message.reply_text(
            "❌ فایل در آرشیو قرار گرفت اما ذخیره اطلاعات "
            "در GitHub ناموفق بود.\n\n"
            "فایل نهایی ثبت نشد. دوباره تلاش کن."
        )

        return ConversationHandler.END

    # -----------------------------------------------------
    # Done
    # -----------------------------------------------------

    context.user_data.pop("admin_upload", None)

    replace_text = (
        "🔄 فایل قبلی با موفقیت جایگزین شد."
        if old_item
        else
        "🆕 فایل جدید با موفقیت ثبت شد."
    )

    await message.reply_text(
        "✅ فایل با موفقیت ثبت شد.\n\n"
        f"{FIELDS[field]}\n"
        f"{GRADES[grade]}\n"
        f"{TYPES[lesson_type]}\n"
        f"📚 {subject_name}\n"
        f"📅 {year}\n\n"
        f"{replace_text}",
        reply_markup=admin_menu(),
    )

    return ConversationHandler.END


async def admin_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop("admin_upload", None)

    if update.callback_query:
        await update.callback_query.answer()

        await update.callback_query.edit_message_text(
            "❌ عملیات لغو شد.",
            reply_markup=admin_menu(),
        )

    return ConversationHandler.END


# =========================================================
# ADMIN CALLBACKS
# =========================================================

async def admin_field_callback(update, context):
    if not is_admin(update):
        return

    query = update.callback_query
    await query.answer()

    field = query.data.split("_")[1]

    await query.edit_message_text(
        f"{FIELDS[field]}\n\n"
        "پایه را انتخاب کن:",
        reply_markup=admin_grades_keyboard(field),
    )


async def admin_grade_callback(update, context):
    if not is_admin(update):
        return

    query = update.callback_query
    await query.answer()

    _, field, grade = query.data.split("_")

    await query.edit_message_text(
        f"{FIELDS[field]} → {GRADES[grade]}\n\n"
        "نوع درس را انتخاب کن:",
        reply_markup=admin_types_keyboard(
            field,
            grade,
        ),
    )


async def admin_type_callback(update, context):
    if not is_admin(update):
        return

    query = update.callback_query
    await query.answer()

    _, field, grade, lesson_type = query.data.split("_")

    await query.edit_message_text(
        f"{FIELDS[field]}\n"
        f"{GRADES[grade]}\n"
        f"{TYPES[lesson_type]}\n\n"
        "درس را انتخاب کن:",
        reply_markup=admin_subjects_keyboard(
            field,
            grade,
            lesson_type,
        ),
    )


async def admin_subject_callback(update, context):
    if not is_admin(update):
        return

    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")

    field = parts[1]
    grade = parts[2]
    lesson_type = parts[3]
    subject_code = "_".join(parts[4:])

    subject_name = next(
        (
            name
            for name, code in SUBJECTS.get(
                (field, grade, lesson_type),
                [],
            )
            if code == subject_code
        ),
        subject_code,
    )

    await query.edit_message_text(
        f"📚 {subject_name}\n\n"
        "سال فایل را انتخاب کن:",
        reply_markup=admin_years_keyboard(
            field,
            grade,
            lesson_type,
            subject_code,
        ),
    )


async def admin_year_callback(update, context):
    if not is_admin(update):
        return

    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")

    field = parts[1]
    grade = parts[2]
    lesson_type = parts[3]
    year = parts[-1]

    subject_code = "_".join(parts[4:-1])

    subject_name = next(
        (
            name
            for name, code in SUBJECTS.get(
                (field, grade, lesson_type),
                [],
            )
            if code == subject_code
        ),
        subject_code,
    )

    context.user_data["admin_upload"] = {
        "field": field,
        "grade": grade,
        "lesson_type": lesson_type,
        "subject_code": subject_code,
        "year": year,
    }

    await query.edit_message_text(
        "📤 آماده دریافت فایل\n\n"
        f"{FIELDS[field]}\n"
        f"{GRADES[grade]}\n"
        f"{TYPES[lesson_type]}\n"
        f"📚 {subject_name}\n"
        f"📅 {year}\n\n"
        "حالا فایل PDF را به صورت Document همین‌جا ارسال کن.\n\n"
        "⚠️ فایل را به صورت «File / Document» بفرست.",
    )

    return ADMIN_FILE


# =========================================================
# ADMIN STATUS
# =========================================================

async def admin_status(update, context):
    if not is_admin(update):
        return

    query = update.callback_query
    await query.answer()

    files, _ = github_get_files()

    total = len(files)

    await query.edit_message_text(
        "📊 وضعیت فایل‌ها\n\n"
        f"تعداد فایل‌های ثبت‌شده: {total}\n\n"
        "اطلاعات فایل‌ها در GitHub ذخیره شده و "
        "خود فایل‌ها در کانال آرشیو خصوصی نگهداری می‌شوند.",
        reply_markup=admin_menu(),
    )


# =========================================================
# USER CALLBACK HANDLER
# =========================================================

async def user_callback(update, context):
    query = update.callback_query

    await query.answer()

    data = query.data

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    if data == "home":
        await query.edit_message_text(
            "🎓 آکادمی مشاوره موحد\n\n"
            "بخش موردنظر را انتخاب کنید:",
            reply_markup=main_menu(update),
        )
        return

    # -----------------------------------------------------
    # FINAL EXAMS
    # -----------------------------------------------------

    if data == "final_exams":
        await show_final_exams(query)
        return

    if data.startswith("ufield_"):
        field = data.split("_")[1]

        if field in FIELDS:
            await show_field(query, field)

        return

    if data.startswith("ugrade_"):
        parts = data.split("_")

        if len(parts) == 3:
            field = parts[1]
            grade = parts[2]

            if field in FIELDS and grade in GRADES:
                await show_grade(
                    query,
                    field,
                    grade,
                )

        return

    if data.startswith("utype_"):
        parts = data.split("_")

        if len(parts) == 4:
            field = parts[1]
            grade = parts[2]
            lesson_type = parts[3]

            if (
                field in FIELDS
                and grade in GRADES
                and lesson_type in TYPES
            ):
                await show_type(
                    query,
                    field,
                    grade,
                    lesson_type,
                )

        return

    if data.startswith("usub_"):
        parts = data.split("_")

        field = parts[1]
        grade = parts[2]
        lesson_type = parts[3]
        subject_code = "_".join(parts[4:])

        await show_subject(
            query,
            field,
            grade,
            lesson_type,
            subject_code,
        )

        return

    if data.startswith("uyear_"):
        parts = data.split("_")

        field = parts[1]
        grade = parts[2]
        lesson_type = parts[3]
        year = parts[-1]

        subject_code = "_".join(parts[4:-1])

        await send_exam_file(
            query,
            context,
            field,
            grade,
            lesson_type,
            subject_code,
            year,
        )

        return

    # -----------------------------------------------------
    # PLACEHOLDERS
    # -----------------------------------------------------

    if data == "mock_exams":
        await query.edit_message_text(
            "📝 آزمون‌های آزمایشی مجموعه\n\n"
            "این بخش به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "↩️ بازگشت",
                        callback_data="home",
                    )
                ]
            ]),
        )
        return

    if data == "notes":
        await query.edit_message_text(
            "📖 جزوات\n\n"
            "این بخش به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "↩️ بازگشت",
                        callback_data="home",
                    )
                ]
            ]),
        )
        return

    if data == "news":
        await query.edit_message_text(
            "📢 اطلاعیه‌ها\n\n"
            "این بخش به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "↩️ بازگشت",
                        callback_data="home",
                    )
                ]
            ]),
        )
        return


# =========================================================
# ADMIN CALLBACK ROUTER
# =========================================================

async def admin_callback_router(update, context):
    data = update.callback_query.data

    if not is_admin(update):
        await update.callback_query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    if data == "admin_panel":
        await admin_panel(
            update,
            context,
        )
        return

    if data == "admin_add":
        await admin_add_start(
            update,
            context,
        )
        return

    if data == "admin_status":
        await admin_status(
            update,
            context,
        )
        return

    if data.startswith("afield_"):
        await admin_field_callback(
            update,
            context,
        )
        return

    if data.startswith("agrade_"):
        await admin_grade_callback(
            update,
            context,
        )
        return

    if data.startswith("atype_"):
        await admin_type_callback(
            update,
            context,
        )
        return

    if data.startswith("asub_"):
        await admin_subject_callback(
            update,
            context,
        )
        return

    if data.startswith("ayear_"):
        await admin_year_callback(
            update,
            context,
        )
        return


# =========================================================
# /ADMIN COMMAND
# =========================================================

async def admin_command(update, context):
    if not is_admin(update):
        await update.message.reply_text(
            "⛔ شما دسترسی مدیریت ندارید."
        )
        return

    await update.message.reply_text(
        "👑 پنل مدیریت",
        reply_markup=admin_menu(),
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):
    logger.exception(
        "Unhandled error: %s",
        context.error,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN environment variable is missing."
        )

    # Render health server
    threading.Thread(
        target=run_health_server,
        daemon=True,
    ).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(False)
        .build()
    )

    # -----------------------------------------------------
    # Admin upload conversation
    # -----------------------------------------------------

    admin_upload_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_year_callback,
                pattern=r"^ayear_",
            )
        ],

        states={
            ADMIN_FILE: [
                MessageHandler(
                    filters.Document.ALL,
                    admin_receive_file,
                )
            ]
        },

        fallbacks=[
            CallbackQueryHandler(
                admin_cancel,
                pattern=r"^admin_cancel$",
            ),
            CommandHandler(
                "start",
                start,
            ),
        ],

        per_user=True,
        per_chat=True,
        allow_reentry=True,
    )

    application.add_handler(
        admin_upload_conversation
    )

    # -----------------------------------------------------
    # Commands
    # -----------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin_command,
        )
    )

    # -----------------------------------------------------
    # Admin callback router
    # -----------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            admin_callback_router,
            pattern=r"^(admin_panel|admin_add|admin_status|afield_|agrade_|atype_|asub_)",
        )
    )

    # -----------------------------------------------------
    # User callbacks
    # -----------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            user_callback,
            pattern=r"^(home|final_exams|ufield_|ugrade_|utype_|usub_|uyear_|mock_exams|notes|news)$",
        )
    )

    # -----------------------------------------------------
    # Error handler
    # -----------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "Movahed bot started. Admin IDs: %s",
        ADMIN_IDS,
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
