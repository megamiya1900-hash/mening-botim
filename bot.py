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
            "Qaysi tilga tarjima qilay?", reply_markup=InlineKeyboardMarkup(LANG_MENU)
        )
        return

    if data.startswith("lang_"):
        USER_LANG[user_id] = data.split("_")[1]
        USER_MODE[user_id] = "translate"
        await query.edit_message_text(
            "Endi menga matn yuboring — men uni tarjima qilib beraman.\n"
            "Bosh menyuga qaytish uchun /start bosing."
        )
        return

    if data == "mode_ocr":
        USER_MODE[user_id] = "ocr"
        await query.edit_message_text(
            "Menga rasm yuboring — men undagi matnni o'qib beraman.\n"
            "Bosh menyuga qaytish uchun /start bosing."
        )
        return

    if data == "mode_currency":
        USER_MODE[user_id] = "currency"
        await query.edit_message_text(
            "Valyuta kursini bilish uchun quyidagi formatda yozing:\n"
            "Masalan: `100 USD UZS`\n\n"
            "Bosh menyuga qaytish uchun /start bosing.",
            parse_mode="Markdown",
        )
        return

    if data == "mode_weather":
        USER_MODE[user_id] = "weather"
        await query.edit_message_text(
            "Qaysi shahar uchun ob-havoni bilmoqchisiz? Shahar nomini yozing.\n"
            "Masalan: `Toshkent`\n\n"
            "Bosh menyuga qaytish uchun /start bosing.",
            parse_mode="Markdown",
        )
        return

    if data == "mode_quiz":
        await send_quiz_question(query.message.chat_id, context)
        return

    if data.startswith("quiz_"):
        await handle_quiz_answer(query, context)
        return


async def send_quiz_question(chat_id, context: ContextTypes.DEFAULT_TYPE):
    question = random.choice(QUIZ_QUESTIONS)
    context.chat_data["current_quiz"] = question
    buttons = [
        [InlineKeyboardButton(opt, callback_data=f"quiz_{i}")]
        for i, opt in enumerate(question["options"])
    ]
    await context.bot.send_message(
        chat_id, f"❓ {question['q']}", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def handle_quiz_answer(query, context: ContextTypes.DEFAULT_TYPE):
    question = context.chat_data.get("current_quiz")
    if not question:
        await query.edit_message_text("Savol muddati tugagan. /start bosing.")
        return
    chosen = int(query.data.split("_")[1])
    if chosen == question["correct"]:
        text = f"✅ To'g'ri! Javob: {question['options'][question['correct']]}"
    else:
        text = (
            f"❌ Noto'g'ri. To'g'ri javob: {question['options'][question['correct']]}"
        )
    await query.edit_message_text(text)
    await send_quiz_question(query.message.chat_id, context)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mode = USER_MODE.get(user_id)
    text = update.message.text

    if mode == "translate":
        target = USER_LANG.get(user_id, "uz")
        try:
            result = GoogleTranslator(source="auto", target=target).translate(text)
            await update.message.reply_text(result)
        except Exception as e:
            logger.exception("Tarjima xatosi")
            await update.message.reply_text(f"Xatolik yuz berdi: {e}")
        return

    if mode == "currency":
        await handle_currency(update, text)
        return

    if mode == "weather":
        await handle_weather(update, text)
        return

    await update.message.reply_text(
        "Iltimos, avval /start orqali menyudan xizmat tanlang."
    )


async def handle_currency(update: Update, text: str):
    parts = text.strip().split()
    if len(parts) != 3:
        await update.message.reply_text(
            "Format noto'g'ri. Masalan: `100 USD UZS`", parse_mode="Markdown"
        )
        return
    amount_str, from_cur, to_cur = parts
    try:
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("Miqdorni raqamda kiriting. Masalan: 100 USD UZS")
        return

    from_cur, to_cur = from_cur.upper(), to_cur.upper()
    try:
        resp = requests.get(f"https://open.er-api.com/v6/latest/{from_cur}", timeout=10)
        data = resp.json()
        if data.get("result") != "success":
            await update.message.reply_text("Valyuta kodi noto'g'ri yoki topilmadi.")
            return
        rate = data["rates"].get(to_cur)
        if rate is None:
            await update.message.reply_text("Bunday valyuta topilmadi.")
            return
        converted = amount * rate
        await update.message.reply_text(
            f"{amount} {from_cur} = {converted:,.2f} {to_cur}"
        )
    except Exception as e:
        logger.exception("Valyuta xatosi")
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")


async def handle_weather(update: Update, city: str):
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "uz"},
            timeout=10,
        ).json()
        results = geo.get("results")
        if not results:
            await update.message.reply_text("Shahar topilmadi. Boshqa nom bilan urinib ko'ring.")
            return
        place = results[0]
        lat, lon = place["latitude"], place["longitude"]
        name = place.get("name", city)

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "timezone": "auto",
            },
            timeout=10,
        ).json()
        cw = weather["current_weather"]
        await update.message.reply_text(
            f"☀️ {name} uchun ob-havo:\n"
            f"🌡 Harorat: {cw['temperature']}°C\n"
            f"💨 Shamol tezligi: {cw['windspeed']} km/soat"
        )
    except Exception as e:
        logger.exception("Ob-havo xatosi")
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USER_MODE.get(user_id) != "ocr":
        await update.message.reply_text(
            "Rasmdan matn olish uchun avval /start orqali OCR xizmatini tanlang."
        )
        return

    await update.message.reply_text("Rasm qayta ishlanmoqda...")
    try:
        photo_file = await update.message.photo[-1].get_file()
        file_bytes = await photo_file.download_as_bytearray()

        resp = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": ("image.jpg", bytes(file_bytes))},
            data={"apikey": OCR_SPACE_API_KEY, "language": "eng", "OCREngine": 2},
            timeout=30,
        )
        result = resp.json()
        parsed = result.get("ParsedResults")
        if not parsed or result.get("IsErroredOnProcessing"):
            await update.message.reply_text(
                "Matnni o'qib bo'lmadi. Rasm sifatini yaxshilab qayta urinib ko'ring."
            )
            return
        extracted_text = parsed[0].get("ParsedText", "").strip()
        if not extracted_text:
            await update.message.reply_text("Rasmda matn topilmadi.")
        else:
            await update.message.reply_text(f"📄 Topilgan matn:\n\n{extracted_text}")
    except Exception as e:
        logger.exception("OCR xatosi")
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN muhit o'zgaruvchisi topilmadi. "
            "export BOT_TOKEN='sizning_tokeningiz' qiling."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
