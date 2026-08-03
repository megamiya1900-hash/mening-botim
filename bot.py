"""
Ko'p xizmatli Telegram bot (5 ta bepul xizmat):
1. Tarjimon
2. OCR (rasmdan matn olish)
3. Valyuta kursi
4. Ob-havo ma'lumoti
5. Test/Viktorina

Ishga tushirish:
    export BOT_TOKEN="sizning_tokeningiz"
    python bot.py

Barcha tashqi API'lar bepul va API kalit talab qilmaydi
(OCR uchun ixtiyoriy: OCR_SPACE_API_KEY muhit o'zgaruvchisi).
"""

import logging
import os
import random

import requests
from deep_translator import GoogleTranslator
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OCR_SPACE_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "helloworld")  # bepul demo kalit

# ---------- Foydalanuvchi holati ----------
# har bir user_id uchun qaysi rejimda ekanini saqlab turamiz
USER_MODE = {}  # {user_id: "translate" | "ocr" | "currency" | "weather"}
USER_LANG = {}  # {user_id: "uz" | "ru" | "en" ...} - tarjima maqsad tili

MAIN_MENU = [
    [InlineKeyboardButton("🌍 Tarjimon", callback_data="mode_translate")],
    [InlineKeyboardButton("🖼 OCR (rasmdan matn)", callback_data="mode_ocr")],
    [InlineKeyboardButton("💱 Valyuta kursi", callback_data="mode_currency")],
    [InlineKeyboardButton("☀️ Ob-havo", callback_data="mode_weather")],
    [InlineKeyboardButton("🧠 Test/Viktorina", callback_data="mode_quiz")],
]

LANG_MENU = [
    [
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Rus", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 Ingliz", callback_data="lang_en"),
    ],
    [InlineKeyboardButton("⬅️ Orqaga", callback_data="back_menu")],
]

QUIZ_QUESTIONS = [
    {
        "q": "O'zbekiston poytaxti qaysi shahar?",
        "options": ["Samarqand", "Toshkent", "Buxoro", "Andijon"],
        "correct": 1,
    },
    {
        "q": "Quyosh tizimidagi eng katta sayyora?",
        "options": ["Yer", "Mars", "Yupiter", "Saturn"],
        "correct": 2,
    },
    {
        "q": "1 kilometr necha metrga teng?",
        "options": ["10", "100", "1000", "10000"],
        "correct": 2,
    },
    {
        "q": "Dunyodagi eng uzun daryo qaysi?",
        "options": ["Amazonka", "Nil", "Amudaryo", "Volga"],
        "correct": 1,
    },
    {
        "q": "Python dasturlash tili qaysi yili yaratilgan?",
        "options": ["1985", "1991", "2000", "1975"],
        "correct": 1,
    },
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USER_MODE.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "Salom! Men foydali xizmatlar botiman.\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(MAIN_MENU),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "back_menu":
        USER_MODE.pop(user_id, None)
        await query.edit_message_text(
            "Bosh menyu. Xizmatni tanlang:", reply_markup=InlineKeyboardMarkup(MAIN_MENU)
        )
        return

    if data == "mode_translate":
        await query.edit_message_text(
            "Qaysi tilga tarjima qilay?", reply_markup=InlineKeyboardMark
