import os
import json
import logging
import threading
import base64
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

# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

ADMIN_IDS = {7847705597}

# کانال خصوصی آرشیو فایل‌ها
ARCHIVE_CHAT_ID = -1003919894012

GITHUB_OWNER = "Mmvhd"
GITHUB_REPO = "movahed-telegram-bot"
GITHUB_FILE = "files.json"
GITHUB_BRANCH = "main"

YEARS = [str(y) for y in range(1404, 1397, -1)]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# DATA
# =========================================================

FIELDS = {
    "exp": "تجربی",
    "math": "ریاضی",
    "hum": "انسانی",
}

GRADES = {
    "11": "یازدهم",
    "12": "دوازدهم",
}

TYPES = {
    "general": "عمومی",
    "special": "اختصاصی",
}


SUBJECTS = {

    # =====================================================
    # EXPERIMENTAL
    # =====================================================

    ("exp", "11", "general"): [
        ("religion2", "دین و زندگی (2)"),
        ("persian2", "فارسی (2)"),
        ("art2", "هنر (2)"),
        ("arabic2", "عربی، زبان قرآن (2)"),
        ("english2", "انگلیسی (2)"),
        ("history_contemporary", "تاریخ معاصر ایران"),
        ("human_environment", "انسان و محیط زیست"),
    ],

    ("exp", "11", "special"): [
        ("biology2", "زیست‌شناسی (2)"),
        ("math2", "ریاضی (2)"),
        ("chemistry2", "شیمی (2)"),
        ("physics2", "فیزیک (2)"),
        ("experimental_lab", "آزمایشگاه علوم تجربی (2)"),
        ("geology", "زمین‌شناسی"),
    ],

    ("exp", "12", "general"): [
        ("persian3", "ادبیات فارسی (3)"),
        ("religion3", "دین و زندگی (3)"),
        ("arabic3", "عربی، زبان قرآن (3)"),
        ("social_identity", "هویت اجتماعی"),
        ("family_lifestyle", "مدیریت خانواده و سبک زندگی"),
        ("english3", "انگلیسی (3)"),
        ("health", "سلامت و بهداشت"),
    ],

    ("exp", "12", "special"): [
        ("biology3", "زیست‌شناسی (3)"),
        ("math3", "ریاضی (3)"),
        ("chemistry3", "شیمی (3)"),
        ("physics3", "فیزیک (3)"),
    ],

    # =====================================================
    # MATHEMATICS
    # =====================================================

    ("math", "11", "general"): [
        ("persian2", "ادبیات فارسی (2)"),
        ("religion2", "دین و زندگی (2)"),
        ("arabic2", "عربی، زبان قرآن (2)"),
        ("art2", "هنر (2)"),
        ("history_contemporary2", "تاریخ معاصر ایران (2)"),
        ("english2", "زبان انگلیسی (2)"),
        ("religious_ethics2", "تعلیمات ادیان الهی و اخلاق (2)"),
        ("geology", "زمین‌شناسی"),
        ("human_environment", "انسان و محیط زیست"),
    ],

    ("math", "11", "special"): [
        ("chemistry2", "شیمی (2)"),
        ("physics2", "فیزیک (2)"),
        ("geometry2", "هندسه (2)"),
        ("calculus1", "حسابان (1)"),
        ("statistics_probability", "آمار و احتمال"),
    ],

    ("math", "12", "general"): [
        ("persian3", "ادبیات فارسی (3)"),
        ("religion3", "دین و زندگی (3)"),
        ("arabic3", "عربی، زبان قرآن (3)"),
        ("english3", "زبان انگلیسی (3)"),
        ("religious_ethics3", "تعلیمات ادیان الهی و اخلاق (3)"),
        ("health", "سلامت و بهداشت"),
        ("social_identity", "هویت اجتماعی"),
    ],

    ("math", "12", "special"): [
        ("chemistry3", "شیمی (3)"),
        ("physics3", "فیزیک (3)"),
        ("geometry3", "هندسه (3)"),
        ("calculus2", "حسابان (2)"),
        ("discrete_math", "ریاضیات گسسته"),
    ],

    # =====================================================
    # HUMANITIES
    # =====================================================

    ("hum", "11", "general"): [
        ("persian2", "فارسی (2)"),
        ("religion2", "دین و زندگی (2)"),
        ("human_environment", "انسان و محیط زیست"),
        ("english2", "زبان انگلیسی (2)"),
        ("art", "هنر"),
        ("family_lifestyle", "مدیریت خانواده و سبک زندگی"),
    ],

    ("hum", "11", "special"): [
        ("math_statistics2", "ریاضی و آمار (2)"),
        ("arabic2", "عربی، زبان قرآن (2)"),
        ("literary_sciences2", "علوم و فنون ادبی (2)"),
        ("philosophy", "فلسفه"),
        ("history2", "تاریخ (2)"),
        ("geography2", "جغرافیای (2)"),
        ("sociology2", "جامعه‌شناسی (2)"),
        ("psychology", "روانشناسی"),
    ],

    ("hum", "12", "general"): [
        ("persian3", "فارسی (3)"),
        ("religion3", "دین و زندگی (3)"),
        ("cultural_analysis", "تحلیل فرهنگی"),
        ("english3", "زبان انگلیسی (3)"),
        ("health", "سلامت و بهداشت"),
        ("family_lifestyle", "مدیریت خانواده و سبک زندگی"),
    ],

    ("hum", "12", "special"): [
        ("math_statistics3", "ریاضی و آمار (3)"),
        ("arabic3", "عربی، زبان قرآن (3)"),
        ("literary_sciences3", "علوم و فنون ادبی (3)"),
        ("philosophy2", "فلسفه (2)"),
        ("history3", "تاریخ (3)"),
        ("geography3", "جغرافیای (3)"),
        ("sociology3", "جامعه‌شناسی (3)"),
    ],
}


# =========================================================
# GITHUB
# =========================================================

def github_url():
    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    )


def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def load_files():
    """
    خواندن files.json از GitHub
    """

    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN is missing")
        return {}

    try:
        response = requests.get(
            github_url(),
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=20,
        )

        if response.status_code == 404:
            return {}

        response.raise_for_status()

        data = response.json()

        content = base64.b64decode(
            data["content"].replace("\n", "")
        ).decode("utf-8")

        if not content.strip():
            return {}

        return json.loads(content)

    except Exception as e:
        logger.exception(
            "Could not load files.json: %s",
            e,
        )
        return {}


def save_files(data):
    """
    ذخیره files.json در GitHub
    """

    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN is missing")
        return False

    try:
        old = requests.get(
            github_url(),
            headers=github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=20,
        )

        sha = None

        if old.status_code == 200:
            sha = old.json().get("sha")

        elif old.status_code != 404:
            old.raise_for_status()

        content = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )

        encoded = base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": "Update files metadata",
            "content": encoded,
            "branch": GITHUB_BRANCH,
        }

        if sha:
            payload["sha"] = sha

        response = requests.put(
            github_url(),
            headers=github_headers(),
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return True

    except Exception as e:
        logger.exception(
            "Could not save files.json: %s",
            e,
        )
        return False


# =========================================================
# HELPERS
# =========================================================

def is_admin(user_id):
    return user_id in ADMIN_IDS


def main_menu(update):
    buttons = [
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

    user = update.effective_user

    if user and is_admin(user.id):
        buttons.append([
            InlineKeyboardButton(
                "👑 پنل مدیریت",
                callback_data="admin_panel",
            )
        ])

    return InlineKeyboardMarkup(buttons)


async def edit_message(query, text, keyboard):
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = (
        "🎓 آکادمی مشاوره موحد\n\n"
        "به ربات آکادمی خوش آمدید.\n"
        "بخش موردنظر خود را انتخاب کنید:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(update),
    )


async def home_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await start(update, context)


# =========================================================
# FINAL EXAMS - USER
# =========================================================

async def show_final_fields(query):
    keyboard = [
        [
            InlineKeyboardButton(
                "🧬 تجربی",
                callback_data="ufield_exp",
            )
        ],
        [
            InlineKeyboardButton(
                "📐 ریاضی",
                callback_data="ufield_math",
            )
        ],
        [
            InlineKeyboardButton(
                "📚 انسانی",
                callback_data="ufield_hum",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="home",
            )
        ],
    ]

    await edit_message(
        query,
        "📚 امتحان‌های نهایی\n\nرشته را انتخاب کنید:",
        keyboard,
    )


async def show_user_grades(query, field):
    keyboard = [
        [
            InlineKeyboardButton(
                "یازدهم",
                callback_data=f"ugrade_{field}_11",
            )
        ],
        [
            InlineKeyboardButton(
                "دوازدهم",
                callback_data=f"ugrade_{field}_12",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="final_exams",
            )
        ],
    ]

    await edit_message(
        query,
        "پایه را انتخاب کنید:",
        keyboard,
    )


async def show_user_types(query, field, grade):
    keyboard = [
        [
            InlineKeyboardButton(
                "📘 عمومی",
                callback_data=f"utype_{field}_{grade}_general",
            )
        ],
        [
            InlineKeyboardButton(
                "📕 اختصاصی",
                callback_data=f"utype_{field}_{grade}_special",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=f"ufield_{field}",
            )
        ],
    ]

    await edit_message(
        query,
        "نوع درس را انتخاب کنید:",
        keyboard,
    )


async def show_user_subjects(
    query,
    field,
    grade,
    type_code,
):
    subjects = SUBJECTS.get(
        (field, grade, type_code),
        [],
    )

    keyboard = []

    for code, title in subjects:
        keyboard.append([
            InlineKeyboardButton(
                title,
                callback_data=(
                    f"usub_{field}_{grade}_"
                    f"{type_code}_{code}"
                ),
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=f"ugrade_{field}_{grade}",
        )
    ])

    await edit_message(
        query,
        "📚 درس موردنظر را انتخاب کنید:",
        keyboard,
    )


async def show_user_years(
    query,
    field,
    grade,
    type_code,
    subject_code,
):
    keyboard = []

    for year in YEARS:
        keyboard.append([
            InlineKeyboardButton(
                year,
                callback_data=(
                    f"uyear_{field}_{grade}_"
                    f"{type_code}_{subject_code}_{year}"
                ),
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=(
                f"utype_{field}_{grade}_{type_code}"
            ),
        )
    ])

    await edit_message(
        query,
        "📅 سال امتحان را انتخاب کنید:",
        keyboard,
    )


# =========================================================
# SEND FINAL FILE
# =========================================================

async def send_final_file(
    query,
    field,
    grade,
    type_code,
    subject_code,
    year,
):
    data = load_files()

    key = (
        f"final|{field}|{grade}|"
        f"{type_code}|{subject_code}|{year}"
    )

    item = data.get(key)

    if not item:
        await query.answer(
            "❌ فایل این بخش هنوز اضافه نشده.",
            show_alert=True,
        )
        return

    archive_message_id = item.get("message_id")

    if not archive_message_id:
        await query.answer(
            "❌ فایل پیدا نشد.",
            show_alert=True,
        )
        return

    try:
        await query.answer(
            "در حال ارسال فایل..."
        )

        await query.message.reply_text(
            "📥 فایل در حال ارسال است..."
        )

        # =================================================
        # FIX:
        # Message object دارای bot نیست.
        # باید از خود CallbackQuery، bot را بگیریم.
        # =================================================

        await query.get_bot().copy_message(
            chat_id=query.message.chat_id,
            from_chat_id=ARCHIVE_CHAT_ID,
            message_id=int(archive_message_id),
        )

        logger.info(
            "File sent successfully: key=%s archive_message_id=%s",
            key,
            archive_message_id,
        )

    except Exception as e:
        logger.exception(
            "Could not send file: %s",
            e,
        )

        # برای ادمین، خطای دقیق را نمایش می‌دهیم
        if query.from_user and is_admin(query.from_user.id):
            await query.message.reply_text(
                "❌ ارسال فایل انجام نشد.\n\n"
                "خطای فنی:\n"
                f"{type(e).__name__}: {e}"
            )
        else:
            await query.message.reply_text(
                "❌ ارسال فایل انجام نشد."
            )


# =========================================================
# USER CALLBACK
# =========================================================

async def user_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    data = query.data

    # ---------------- HOME ----------------

    if data == "home":
        await query.answer()

        await query.edit_message_text(
            "🎓 آکادمی مشاوره موحد\n\n"
            "بخش موردنظر را انتخاب کنید:",
            reply_markup=main_menu(update),
        )
        return

    # ---------------- FINAL EXAMS ----------------

    if data == "final_exams":
        await query.answer()
        await show_final_fields(query)
        return

    if data.startswith("ufield_"):
        await query.answer()

        field = data.replace(
            "ufield_",
            "",
            1,
        )

        if field not in FIELDS:
            return

        await show_user_grades(
            query,
            field,
        )
        return

    if data.startswith("ugrade_"):
        await query.answer()

        parts = data.split("_")

        if len(parts) == 3:
            field = parts[1]
            grade = parts[2]

            if field not in FIELDS or grade not in GRADES:
                return

            await show_user_types(
                query,
                field,
                grade,
            )

        return

    if data.startswith("utype_"):
        await query.answer()

        parts = data.split("_")

        if len(parts) == 4:
            field = parts[1]
            grade = parts[2]
            type_code = parts[3]

            if (
                field not in FIELDS
                or grade not in GRADES
                or type_code not in TYPES
            ):
                return

            await show_user_subjects(
                query,
                field,
                grade,
                type_code,
            )

        return

    if data.startswith("usub_"):
        await query.answer()

        parts = data.split("_")

        if len(parts) >= 5:
            field = parts[1]
            grade = parts[2]
            type_code = parts[3]
            subject_code = "_".join(parts[4:])

            if (
                field not in FIELDS
                or grade not in GRADES
                or type_code not in TYPES
            ):
                return

            await show_user_years(
                query,
                field,
                grade,
                type_code,
                subject_code,
            )

        return

    if data.startswith("uyear_"):
        parts = data.split("_")

        if len(parts) >= 6:
            field = parts[1]
            grade = parts[2]
            type_code = parts[3]
            year = parts[-1]
            subject_code = "_".join(parts[4:-1])

            await send_final_file(
                query,
                field,
                grade,
                type_code,
                subject_code,
                year,
            )

        return

    # ---------------- OTHER MAIN SECTIONS ----------------

    if data == "mock_exams":
        await query.answer()

        await query.edit_message_text(
            "📝 آزمون‌های آزمایشی مجموعه\n\n"
            "این بخش به‌زودی تکمیل می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="home",
                    )
                ]
            ]),
        )
        return

    if data == "notes":
        await query.answer()

        await query.edit_message_text(
            "📖 جزوات\n\n"
            "جزوات موجود در این بخش نمایش داده می‌شوند.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="home",
                    )
                ]
            ]),
        )
        return

    if data == "news":
        await query.answer()

        await query.edit_message_text(
            "📢 اطلاعیه‌ها\n\n"
            "اطلاعیه‌های آکادمی در این بخش قرار می‌گیرند.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="home",
                    )
                ]
            ]),
        )
        return


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ دسترسی ندارید."
        )
        return

    await update.message.reply_text(
        "👑 پنل مدیریت\n\n"
        "عملیات موردنظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ افزودن فایل",
                    callback_data="admin_add",
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 افزودن اطلاعیه",
                    callback_data="admin_add_news",
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 وضعیت",
                    callback_data="admin_status",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home",
                )
            ],
        ]),
    )


async def admin_panel_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await query.answer()

    await query.edit_message_text(
        "👑 پنل مدیریت\n\n"
        "عملیات موردنظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ افزودن فایل",
                    callback_data="admin_add",
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 افزودن اطلاعیه",
                    callback_data="admin_add_news",
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 وضعیت",
                    callback_data="admin_status",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home",
                )
            ],
        ]),
    )


# =========================================================
# ADMIN ADD FILE
# =========================================================

ADMIN_FILE = 1


async def admin_add_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return ConversationHandler.END

    await query.answer()

    await query.edit_message_text(
        "➕ افزودن محتوا\n\n"
        "بخش موردنظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📚 امتحان‌های نهایی",
                    callback_data="afinal",
                )
            ],
            [
                InlineKeyboardButton(
                    "📝 آزمون‌های آزمایشی",
                    callback_data="amock",
                )
            ],
            [
                InlineKeyboardButton(
                    "📖 جزوات",
                    callback_data="anotes",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="admin_panel",
                )
            ],
        ]),
    )

    return ConversationHandler.END


# =========================================================
# ADMIN FINAL EXAM UPLOAD FLOW
# =========================================================

async def admin_final_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return ConversationHandler.END

    await query.answer()

    await query.edit_message_text(
        "📚 افزودن امتحان نهایی\n\n"
        "رشته را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🧬 تجربی",
                    callback_data="afield_exp",
                )
            ],
            [
                InlineKeyboardButton(
                    "📐 ریاضی",
                    callback_data="afield_math",
                )
            ],
            [
                InlineKeyboardButton(
                    "📚 انسانی",
                    callback_data="afield_hum",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="admin_add",
                )
            ],
        ]),
    )


async def admin_field_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await query.answer()

    field = query.data.replace(
        "afield_",
        "",
        1,
    )

    if field not in FIELDS:
        return

    await query.edit_message_text(
        "پایه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "یازدهم",
                    callback_data=f"agrade_{field}_11",
                )
            ],
            [
                InlineKeyboardButton(
                    "دوازدهم",
                    callback_data=f"agrade_{field}_12",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="afinal",
                )
            ],
        ]),
    )


async def admin_grade_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await query.answer()

    parts = query.data.split("_")

    if len(parts) != 3:
        return

    field = parts[1]
    grade = parts[2]

    if field not in FIELDS or grade not in GRADES:
        return

    await query.edit_message_text(
        "نوع درس را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📘 عمومی",
                    callback_data=(
                        f"atype_{field}_{grade}_general"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "📕 اختصاصی",
                    callback_data=(
                        f"atype_{field}_{grade}_special"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"afield_{field}",
                )
            ],
        ]),
    )


async def admin_type_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await query.answer()

    parts = query.data.split("_")

    if len(parts) != 4:
        return

    field = parts[1]
    grade = parts[2]
    type_code = parts[3]

    if (
        field not in FIELDS
        or grade not in GRADES
        or type_code not in TYPES
    ):
        return

    subjects = SUBJECTS.get(
        (field, grade, type_code),
        [],
    )

    keyboard = []

    for code, title in subjects:
        keyboard.append([
            InlineKeyboardButton(
                title,
                callback_data=(
                    f"asub_{field}_{grade}_"
                    f"{type_code}_{code}"
                ),
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=(
                f"agrade_{field}_{grade}"
            ),
        )
    ])

    await query.edit_message_text(
        "📚 درس را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_subject_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return ConversationHandler.END

    await query.answer()

    parts = query.data.split("_")

    if len(parts) < 5:
        return ConversationHandler.END

    field = parts[1]
    grade = parts[2]
    type_code = parts[3]
    subject_code = "_".join(parts[4:])

    if (
        field not in FIELDS
        or grade not in GRADES
        or type_code not in TYPES
    ):
        return ConversationHandler.END

    context.user_data["upload_meta"] = {
        "category": "final",
        "field": field,
        "grade": grade,
        "type": type_code,
        "subject": subject_code,
    }

    keyboard = []

    for year in YEARS:
        keyboard.append([
            InlineKeyboardButton(
                year,
                callback_data=f"ayear_{year}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "❌ لغو",
            callback_data="admin_cancel",
        )
    ])

    await query.edit_message_text(
        "📅 سال امتحان را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ADMIN_FILE


async def admin_year_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return ConversationHandler.END

    await query.answer()

    year = query.data.replace(
        "ayear_",
        "",
        1,
    )

    if year not in YEARS:
        return ConversationHandler.END

    meta = context.user_data.get("upload_meta")

    if not meta:
        await query.edit_message_text(
            "❌ اطلاعات آپلود پیدا نشد."
        )
        return ConversationHandler.END

    meta["year"] = year
    context.user_data["upload_meta"] = meta

    await query.edit_message_text(
        "📎 حالا فایل را به صورت PDF یا Document ارسال کن.\n\n"
        "فایل جدید جای فایل قبلی همین بخش را می‌گیرد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="admin_cancel",
                )
            ]
        ]),
    )

    return ADMIN_FILE


async def admin_receive_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    if not update.message or not update.message.document:
        await update.message.reply_text(
            "❌ لطفاً فایل را به صورت Document ارسال کن."
        )
        return ADMIN_FILE

    document = update.message.document

    meta = context.user_data.get("upload_meta")

    if not meta:
        await update.message.reply_text(
            "❌ اطلاعات آپلود پیدا نشد. دوباره از پنل شروع کن."
        )
        return ConversationHandler.END

    # -----------------------------------------
    # دریافت اطلاعات فایل
    # -----------------------------------------

    old_data = load_files()

    key = (
        f"final|{meta['field']}|{meta['grade']}|"
        f"{meta['type']}|{meta['subject']}|{meta['year']}"
    )

    old_item = old_data.get(key)

    # -----------------------------------------
    # حذف فایل قبلی از آرشیو
    # -----------------------------------------

    if old_item and old_item.get("message_id"):
        try:
            await context.bot.delete_message(
                chat_id=ARCHIVE_CHAT_ID,
                message_id=int(
                    old_item["message_id"]
                ),
            )

            logger.info(
                "Old archive message deleted: %s",
                old_item["message_id"],
            )

        except Exception as e:
            logger.warning(
                "Could not delete old archive message: %s",
                e,
            )

    # -----------------------------------------
    # کپی فایل به کانال آرشیو
    # -----------------------------------------

    try:
        copied = await context.bot.copy_message(
            chat_id=ARCHIVE_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )

    except Exception as e:
        logger.exception(
            "Could not copy file to archive: %s",
            e,
        )

        await update.message.reply_text(
            "❌ انتقال فایل به آرشیو انجام نشد.\n\n"
            f"خطای فنی: {type(e).__name__}: {e}"
        )

        return ADMIN_FILE

    # -----------------------------------------
    # ذخیره metadata
    # -----------------------------------------

    old_data[key] = {
        "category": "final",
        "field": meta["field"],
        "grade": meta["grade"],
        "type": meta["type"],
        "subject": meta["subject"],
        "year": meta["year"],
        "message_id": copied.message_id,
        "file_name": document.file_name,
        "file_size": document.file_size,
    }

    if not save_files(old_data):
        await update.message.reply_text(
            "⚠️ فایل به آرشیو منتقل شد، "
            "ولی ذخیره اطلاعات در GitHub ناموفق بود."
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "✅ فایل با موفقیت اضافه شد.\n\n"
        "📦 فایل در آرشیو ذخیره شد.\n"
        "🔄 اگر فایل قبلی وجود داشت، جایگزین شد.\n"
        "🗂 اطلاعات در GitHub ذخیره شد."
    )

    context.user_data.pop(
        "upload_meta",
        None,
    )

    return ConversationHandler.END


async def admin_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    context.user_data.pop(
        "upload_meta",
        None,
    )

    await query.edit_message_text(
        "❌ عملیات لغو شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "👑 پنل مدیریت",
                    callback_data="admin_panel",
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home",
                )
            ],
        ]),
    )

    return ConversationHandler.END


# =========================================================
# OTHER ADMIN CONTENT
# =========================================================

async def admin_other_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await query.answer()

    category = query.data

    if category == "amock":
        title = "📝 آزمون‌های آزمایشی"

    elif category == "anotes":
        title = "📖 جزوات"

    else:
        title = "بخش"

    await query.edit_message_text(
        f"{title}\n\n"
        "این بخش آماده دریافت ساختار اختصاصی خودش است.\n\n"
        "برای این قسمت می‌توانیم دسته‌بندی، درس، پایه، "
        "سال و فایل‌های متعدد تعریف کنیم.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="admin_add",
                )
            ]
        ]),
    )


async def admin_add_news(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await query.answer()

    await query.edit_message_text(
        "📢 افزودن اطلاعیه\n\n"
        "برای اضافه‌کردن اطلاعیه، متن اطلاعیه را ارسال کن.\n\n"
        "ساختار اطلاعیه‌ها در GitHub ذخیره خواهد شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="admin_panel",
                )
            ]
        ]),
    )


# =========================================================
# ADMIN STATUS
# =========================================================

async def admin_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    await query.answer()

    data = load_files()

    final_count = 0
    mock_count = 0
    notes_count = 0
    news_count = 0

    for item in data.values():

        category = item.get("category")

        if category == "final":
            final_count += 1

        elif category == "mock":
            mock_count += 1

        elif category == "notes":
            notes_count += 1

        elif category == "news":
            news_count += 1

    await query.edit_message_text(
        "📋 وضعیت ربات\n\n"
        f"📚 امتحان‌های نهایی: {final_count}\n"
        f"📝 آزمون‌های آزمایشی: {mock_count}\n"
        f"📖 جزوات: {notes_count}\n"
        f"📢 اطلاعیه‌ها: {news_count}\n\n"
        f"📦 مجموع آیتم‌ها: {len(data)}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data="admin_status",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="admin_panel",
                )
            ],
        ]),
    )


# =========================================================
# ADMIN CALLBACK ROUTER
# =========================================================

async def admin_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(update.effective_user.id):
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True,
        )
        return

    data = query.data

    if data == "admin_panel":
        await admin_panel_callback(
            update,
            context,
        )
        return

    if data == "admin_add":
        await admin_add_callback(
            update,
            context,
        )
        return

    if data == "afinal":
        await admin_final_callback(
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
        # این callback باید توسط ConversationHandler مدیریت شود
        return

    if data.startswith("ayear_"):
        # این callback باید توسط ConversationHandler مدیریت شود
        return

    if data == "amock" or data == "anotes":
        await admin_other_content(
            update,
            context,
        )
        return

    if data == "admin_add_news":
        await admin_add_news(
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


# =========================================================
# HEALTH SERVER FOR RENDER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8",
        )

        self.end_headers()

        self.wfile.write(
            b"Movahed Telegram Bot is running."
        )

    def log_message(self, format, *args):
        return


def run_health_server():

    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler,
    )

    logger.info(
        "Health server running on port %s",
        port,
    )

    server.serve_forever()


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not configured."
        )

    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN is not configured."
        )

    # -----------------------------------------
    # Render health server
    # -----------------------------------------

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

    # =====================================================
    # ADMIN UPLOAD CONVERSATION
    # =====================================================

    admin_upload_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                admin_subject_callback,
                pattern=r"^asub_",
            )
        ],

        states={
            ADMIN_FILE: [

                CallbackQueryHandler(
                    admin_year_callback,
                    pattern=r"^ayear_",
                ),

                MessageHandler(
                    filters.Document.ALL,
                    admin_receive_file,
                ),

                CallbackQueryHandler(
                    admin_cancel,
                    pattern=r"^admin_cancel$",
                ),
            ]
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                admin_cancel,
            ),

            CallbackQueryHandler(
                admin_cancel,
                pattern=r"^admin_cancel$",
            ),
        ],

        allow_reentry=True,
    )

    application.add_handler(
        admin_upload_conversation
    )

    # =====================================================
    # COMMANDS
    # =====================================================

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "home",
            home_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin_command,
        )
    )

    # =====================================================
    # ADMIN CALLBACKS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            admin_callback_router,
            pattern=(
                r"^(admin_panel|admin_add|afinal|"
                r"afield_|agrade_|atype_|asub_|ayear_|"
                r"amock|anotes|admin_add_news|admin_status)"
            ),
        )
    )

    # =====================================================
    # USER CALLBACKS
    # =====================================================

    application.add_handler(
        CallbackQueryHandler(
            user_callback,
            pattern=(
                r"^(home|final_exams|"
                r"ufield_|ugrade_|utype_|usub_|uyear_|"
                r"mock_exams|notes|news)"
            ),
        )
    )

    logger.info(
        "Movahed Telegram Bot started successfully."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
