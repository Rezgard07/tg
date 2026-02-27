import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from deep_translator import GoogleTranslator
from aiohttp import web
from pyaspeller import YandexSpeller

# 1. Сначала настройки
TOKEN = "8354164344:AAGfLAdD6_tRY6wFc5_2gerCTZ9HIy-wBjU"
bot = Bot(token=TOKEN)
dp = Dispatcher() # Диспетчер создан! Теперь ошибки "is not defined" не будет
speller = YandexSpeller()

# 2. Веб-сервер для Render
async def handle(request):
    return web.Response(text="Бот rezgard работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

# 3. Команды бота
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Дарова! Это бот от <b>rezgard</b>.\n"
        "Пиши текст — я исправлю ошибки и переведу!",
        parse_mode="HTML"
    )

@dp.message()
async def handle_message(message: types.Message):
    if not message.text: return
    text = message.text
    try:
        # Проверка ошибок
        corrected_text = speller.spelled(text)
        has_errors = "❌ Исправлены ошибки" if text != corrected_text else "✅ Ошибок нет"
        
        # Перевод
        if any(c in "абвгдейёжзийклмнопрстуфхцчшщъыьэюя" for c in text.lower()):
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            direction = "🇷🇺 RU ➡️ 🇺🇸 EN"
        else:
            translated = GoogleTranslator(source='auto', target='ru').translate(text)
            direction = "🇺🇸 EN ➡️ 🇷🇺 RU"

        await message.answer(
            f"<b>Статус:</b> {has_errors}\n"
            f"<b>Правка:</b> {corrected_text}\n\n"
            f"<b>{direction}:</b>\n<code>{translated}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Ошибка обработки текста.")

# 4. Запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
