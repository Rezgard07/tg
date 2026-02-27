import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from deep_translator import GoogleTranslator
from aiohttp import web

# Твой токен уже здесь
TOKEN = "8354164344:AAGfLAdD6_tRY6wFc5_2gerCTZ9HIy-wBjU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Секция для Render (чтобы не засыпал и не выдавал ошибку порта) ---
async def handle(request):
    return web.Response(text="Бот запущен и работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()
# -------------------------------------------------------------------

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Дарова! Это бот, сделанный с помощью овнера-разраба <b>rezgard</b>.\n\n"
        "Я могу:\n"
        "1. Перевести текст (RU ↔ EN).\n"
        "2. Просто пришли мне предложение, и я его переведу!",
        parse_mode="HTML"
    )

@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    text = message.text
    
    try:
        # Автоматическое определение языка и перевод
        # Если есть русские буквы — переводим на английский, иначе — на русский
        if any(c in "абвгдейёжзийклмнопрстуфхцчшщъыьэюя" for c in text.lower()):
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            direction = "🇷🇺 RU ➡️ 🇺🇸 EN"
        else:
            translated = GoogleTranslator(source='auto', target='ru').translate(text)
            direction = "🇺🇸 EN ➡️ 🇷🇺 RU"
            
        response = (
            f"<b>Оригинал:</b> {text}\n\n"
            f"<b>{direction}:</b>\n<code>{translated}</code>"
        )
    except Exception as e:
        response = "⚠️ Ошибка при переводе. Попробуй позже."
        logging.error(f"Error: {e}")

    await message.answer(response, parse_mode="HTML")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Запускаем веб-сервер для Render параллельно с ботом
    asyncio.create_task(start_web_server())
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот остановлен")