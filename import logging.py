import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from textblob import TextBlob

# Вставь сюда свой токен от @BotFather
TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Дарова! Это бот, сделанный с помощью овнера-разраба rezgard.\n\n"
        "Я могу:\n"
        "1. Проверить орфографию (просто пришли текст).\n"
        "2. Перевести текст (RU -> EN или EN -> RU).\n"
        "Используй кнопки ниже!"
    )

@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    blob = TextBlob(text)
    
    # 1. Проверка орфографии (наиболее эффективно для EN, для RU база ограничена)
    corrected_text = str(blob.correct())
    
    # 2. Перевод (автоматическое определение направления)
    try:
        # Пытаемся определить язык и перевести
        if blob.detect_language() == 'ru':
            translated = str(blob.translate(to='en'))
            direction = "🇷🇺 RU ➡️ 🇺🇸 EN"
        else:
            translated = str(blob.translate(to='ru'))
            direction = "🇺🇸 EN ➡️ 🇷🇺 RU"
    except Exception:
        translated = "Не удалось перевести (возможно, текст слишком короткий или уже на нужном языке)."
        direction = "Перевод"

    response = (
        f"<b>Исправленный текст:</b>\n{corrected_text}\n\n"
        f"<b>{direction}:</b>\n{translated}"
    )
    
    await message.answer(response, parse_mode="HTML")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())